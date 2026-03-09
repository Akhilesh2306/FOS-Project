"""BaseFOSAgent — the abstract class that all FOS agents extend.

Graph compilation, invocation, state inspection, and crash recovery.
Node-level retry lives in node_wrapper.py; tracing lives in tracing.py.
"""

# Import external libraries
from __future__ import annotations

import logging
from typing import Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone

# Import langgraph specific components
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

# Import internal modules
from ..config import AgentSettings
from graph.tools import AgentToolkit
from graph.node_wrapper import create_node
from graph.tracing import configure_tracing
from graph.state import AgentStatus, BaseAgentState
from graph.errors import AgentConfigError, FOSAgentError, RetryableError

# Setup logging
logger = logging.getLogger(__name__)


class BaseFOSAgent(ABC):
    """Abstract base for all FOS agents.

    Subclasses MUST define:
        agent_name  — class attribute, e.g. "detection", "nba"
        build_graph — adds nodes and edges to the StateGraph builder

    Subclasses MAY override:
        state_schema — to extend BaseAgentState with agent-specific fields
    """

    # ── Class Attributes (overridden by child agents) ─────────────────
    agent_name: str = ""
    """Must be set by every child class (e.g. 'detection', 'nba', 'rag')."""

    state_schema: type[BaseAgentState] = BaseAgentState
    """TypedDict class that defines this agent's state."""

    # ══════════════════════════════════════════════════════════════════
    # CONSTUCTOR
    # ══════════════════════════════════════════════════════════════════
    def __init__(
        self,
        settings: AgentSettings,
        toolkit: AgentToolkit,
        checkpointer: Any | None = None,
    ) -> None:
        """Initialize the agent with its dependencies.

        
        :param settings:     Environment-driven configuration (config.py).
        :param toolkit:      Bundle of tool functions (query, LLM, write, publish).
        :param checkpointer: LangGraph checkpointer for state persistence.
                              Defaults to MemorySaver (in-memory) for local dev.
                              In production, pass a SnowflakeSaver instance.

        :raises AgentConfigError: If agent_name is not set by the child class.
        """
        if not self.agent_name:
            raise AgentConfigError(
                f"{self.__class__.__name__} must define 'agent_name' "
                "as a class attribute."
            )

        self.settings = settings
        self.toolkit = toolkit
        self.checkpointer = checkpointer or MemorySaver()

        configure_tracing(self.agent_name, self.settings)

        self._compiled_graph = self._compile()

        logger.info(
            "Agent initialized: name=%s, schema=%s, checkpointer=%s",
            self.agent_name,
            self.state_schema.__name__,
            type(self.checkpointer).__name__,
        )

    # ══════════════════════════════════════════════════════════════════
    # GRAPH COMPILATION
    # ══════════════════════════════════════════════════════════════════

    @abstractmethod
    def build_graph(self, builder: StateGraph) -> StateGraph:
        """Define the agent's graph topology.

        Add nodes and edges to the builder, then return it.
        Use self.make_node() to wrap node functions with retry/status.
        """


    def _compile(self) -> CompiledStateGraph:
        """Build, populate, and compile the agent graph (called once in __init__)."""
        builder = StateGraph(self.state_schema)
        builder = self.build_graph(builder)
        return builder.compile(checkpointer=self.checkpointer)

    # ══════════════════════════════════════════════════════════════════
    # NODE CREATION (delegates to node_wrapper module)
    # ══════════════════════════════════════════════════════════════════

    def make_node(
        self,
        node_name: str,
        func: callable,
        *,
        status: AgentStatus | None = None,
    ) -> callable:
        """Wrap a node function with retry, status tracking, and trace.
        Delegates to graph.node_wrapper.create_node().
        """
        return create_node(
            agent_name=self.agent_name,
            settings=self.settings,
            node_name=node_name,
            func=func,
            status=status,
        )

    # ══════════════════════════════════════════════════════════════════
    # INVOCATION
    # ══════════════════════════════════════════════════════════════════

    def invoke(
        self,
        input_state: dict[str, Any],
        *,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the agent graph synchronously.

        If a thread_id matches a prior checkpoint, the graph resumes
        from the last successful node (crash recovery).

        :returns: Final state dict with status == "complete" or "failed".
        """

        thread_id = thread_id or self._generate_thread_id(input_state)
        config = {"configurable": {"thread_id": thread_id}}
        initial = self._prepare_initial_state(input_state, thread_id)

        logger.info(
            f"[{self.agent_name}] Starting invocation: thread_id={thread_id}, opp_id={input_state.get('opportunity_id', 'N/A')}",
        )

        try:
            result = self._compiled_graph.invoke(initial, config)
            result["status"] = AgentStatus.COMPLETE.value
            result["completed_at"] = _utc_now_iso()

            logger.info(
                f"[{self.agent_name}] Invocation complete: thread_id={thread_id}, nodes={result.get('node_trace', [])}",
            )
            return result

        except FOSAgentError as exc:
            logger.error(
                f"[{self.agent_name}] Invocation failed: thread_id={thread_id}, error={exc}",
                exc_info=True,
            )
            return self._build_error_state(thread_id, input_state, exc)

        except Exception as exc:
            logger.critical(
                f"[{self.agent_name}] Unexpected error: thread_id={thread_id}, error={exc}",
                exc_info=True,
            )
            return self._build_error_state(thread_id, input_state, exc)


    async def ainvoke(
        self,
        input_state: dict[str, Any],
        *,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the agent graph asynchronously (for FastAPI)."""
        thread_id = thread_id or self._generate_thread_id(input_state)
        config = {"configurable": {"thread_id": thread_id}}
        initial = self._prepare_initial_state(input_state, thread_id)

        logger.info(
            f"[{self.agent_name}] Starting async invocation: thread_id={thread_id}",
        )

        try:
            result = await self._compiled_graph.ainvoke(initial, config)
            result["status"] = AgentStatus.COMPLETE.value
            result["completed_at"] = _utc_now_iso()
            return result

        except FOSAgentError as exc:
            return self._build_error_state(thread_id, input_state, exc)

        except Exception as exc:
            logger.critical(
                f"[{self.agent_name}] Unexpected async error: thread_id={thread_id}, error={exc}",
                exc_info=True,
            )
            return self._build_error_state(thread_id, input_state, exc)

    # ══════════════════════════════════════════════════════════════════
    # STATE INSPECTION
    # ══════════════════════════════════════════════════════════════════

    def get_state(self, thread_id: str) -> dict[str, Any] | None:
        """Retrieve the latest checkpointed state for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        try:
            snapshot = self._compiled_graph.get_state(config)
            if snapshot and snapshot.values:
                return dict(snapshot.values)
            return None
        except Exception:
            logger.warning(
                f"[{self.agent_name}] Failed to retrieve state for thread_id={thread_id}",
                exc_info=True,
            )
            return None

    # ══════════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _generate_thread_id(self, input_state: dict[str, Any]) -> str:
        """Format: {agent_name}_{opportunity_id}_{timestamp}"""
        opp_id = input_state.get("opportunity_id", "noop")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"{self.agent_name}_{opp_id}_{timestamp}"


    def _prepare_initial_state(
        self,
        input_state: dict[str, Any],
        thread_id: str,
    ) -> dict[str, Any]:
        """Merge user input with standard initial fields."""
        return {
            "agent_name": self.agent_name,
            "thread_id": thread_id,
            "status": AgentStatus.PENDING.value,
            "started_at": _utc_now_iso(),
            "retry_count": 0,
            **input_state,
        }


    def _build_error_state(
        self,
        thread_id: str,
        input_state: dict[str, Any],
        error: Exception,
    ) -> dict[str, Any]:
        """Build a state dict representing a failed run."""
        error_type = (
            "retryable" if isinstance(error, RetryableError) else "permanent"
        )
        return {
            "agent_name": self.agent_name,
            "thread_id": thread_id,
            "opportunity_id": input_state.get("opportunity_id", ""),
            "status": AgentStatus.FAILED.value,
            "started_at": input_state.get("started_at", _utc_now_iso()),
            "completed_at": _utc_now_iso(),
            "error": {
                "type": error_type,
                "message": str(error),
                "exception_class": type(error).__name__,
            },
        }


def _utc_now_iso() -> str:
    """UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()