"""FOS Agent Graph — LangGraph-based agent framework.

Public API:
    BaseFOSAgent   — abstract base class for all agents
    BaseAgentState — state TypedDict shared by all agents
    AgentStatus    — lifecycle status enum
    AgentToolkit   — dependency bundle injected into agents
    Errors         — exception hierarchy
"""

from graph.base import BaseFOSAgent
from graph.tools import AgentToolkit
from graph.state import AgentStatus, BaseAgentState
from graph.errors import (
    AgentConfigError,
    CortexLLMError,
    CortexTimeoutError,
    EventHubsError,
    FOSAgentError,
    HybridTableWriteError,
    PermanentError,
    RetryableError,
    SemanticGuardError,
)

__all__ = [
    # Core
    "BaseFOSAgent",
    "BaseAgentState",
    "AgentStatus",
    "AgentToolkit",
    # Errors
    "FOSAgentError",
    "RetryableError",
    "PermanentError",
    "SemanticGuardError",
    "CortexLLMError",
    "CortexTimeoutError",
    "HybridTableWriteError",
    "EventHubsError",
    "AgentConfigError",
]
