"""LangSmith tracing configuration for FOS agents."""

# Import external libraries
from __future__ import annotations

import os
import logging

# Import internal modules
from config import AgentSettings

# Setup logging
logger = logging.getLogger(__name__)


def configure_tracing(agent_name: str, settings: AgentSettings) -> None:
    """
    Set up LangSmith tracing via environment variables.

    LangGraph's tracing is env-var driven. When these vars are set
    BEFORE graph compilation, all node executions and LLM calls are
    automatically traced to LangSmith:

        LANGCHAIN_TRACING_V2=true
        LANGCHAIN_API_KEY=ls-...
        LANGCHAIN_PROJECT=fos-agents

    
    :param agent_name: Used for log messages only.
    :param settings:   AgentSettings containing LangSmith credentials.
    """
    if not settings.has_langsmith_config:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        logger.debug(f"[{agent_name}] LangSmith tracing disabled")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info(
        f"[{agent_name}] LangSmith tracing enabled: project={settings.langsmith_project}"
    )
