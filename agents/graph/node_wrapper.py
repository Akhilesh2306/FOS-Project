"""Node wrapper — adds retry, status tracking, and execution trace to every node."""

# Import external libraries
from __future__ import annotations

import time
import random
import logging
from typing import Any

# Import internal modules
from config import AgentSettings
from graph.state import AgentStatus
from graph.errors import PermanentError, RetryableError

# Setup logging
logger = logging.getLogger(__name__)


def create_node(
    agent_name: str,
    settings: AgentSettings,
    node_name: str,
    func: callable,
    *,
    status: AgentStatus | None = None,
) -> callable:
    """Wrap a node function with standard FOS behavior.

    Adds to every node:
      1. Status tracking — updates state["status"] on entry
      2. Execution trace — appends node_name to state["node_trace"]
      3. Retry logic — RetryableErrors retried with exponential backoff
      4. Error separation — PermanentErrors propagate immediately

    :param agent_name: The owning agent's name (for logging).
    :param settings:   AgentSettings with retry configuration.
    :param node_name:  Human-readable name matching builder.add_node().
    :param func:       Node logic. Receives state dict, returns partial update dict.
    :param status:     AgentStatus to set when this node starts.
                       None means "don't change status".

    :returns: A wrapped function with the signature LangGraph expects:
              (state: dict) -> dict
    """

    def wrapped(state: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"[{agent_name}] Entering node: {node_name}")

        updates: dict[str, Any] = {
            "current_node": node_name,
            "node_trace": [node_name],
        }
        if status is not None:
            updates["status"] = status.value

        # ── Retry Loop ────────────────────────────────────────
        last_error: Exception | None = None

        for attempt in range(1, settings.max_retries + 2):
            try:
                result = func(state)

                if result and isinstance(result, dict):
                    updates.update(result)

                logger.info(
                    f"[{agent_name}] Node completed: {node_name} (attempt {attempt})"
                )
                return updates

            except RetryableError as exc:
                last_error = exc

                if attempt > settings.max_retries:
                    logger.error(
                        f"[{agent_name}] Node {node_name} failed after {attempt} attempts: {exc}"
                    )
                    break

                delay = min(
                    settings.retry_base_delay_seconds * (2 ** (attempt - 1)),
                    settings.retry_max_delay_seconds,
                )
                jitter = random.uniform(0, 1)  # noqa: S311
                total_delay = delay + jitter

                logger.warning(
                    f"[{agent_name}] Node {node_name} retryable error (attempt {attempt}/{settings.max_retries}), "
                    f"retrying in {total_delay:.1f}s: {exc}"
                )
                time.sleep(total_delay)

            except PermanentError:
                logger.error(
                    f"[{agent_name}] Node {node_name} permanent error",
                    exc_info=True,
                )
                raise

        assert last_error is not None 
        raise last_error

    wrapped.__name__ = f"{node_name}_wrapped"
    wrapped.__qualname__ = f"{agent_name}.{node_name}"
    return wrapped
