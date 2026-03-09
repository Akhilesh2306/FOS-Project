"""Base state schema shared by all FOS agents."""

# Import external libraries
import operator
from enum import Enum
from typing import Annotated, Any, TypedDict


class AgentStatus(str, Enum):
    """
    Lifecycle phases for agents.
    Every agent follows same lifecycle, but may skip some phases depending on the use case.
    PENDING -> FETCHING_CONTEXT -> CHECKING_HISTORY -> GENERATING -> RANKING -> WRITING -> PUBLISHING -> COMPLETE
    """

    PENDING = "pending"
    FETCHING_CONTEXT = "fetching_context"
    CHECKING_HISTORY = "checking_history"
    GENERATING = "generating"
    RANKING = "ranking"
    WRITING = "writing"
    PUBLISHING = "publishing"
    COMPLETE = "complete"
    FAILED = "failed"


class BaseAgentState(TypedDict, total=False):
    """ 
    Base state schema shared by all FOS agents.
    """

    # === Lifecycle Tracking ===
    status: str
    current_node: str
    started_at: str
    completed_at: str

    # === Deal Context ===
    deal_context: dict[str, Any]

    # === Error Tracking ===
    error: dict[str, Any]
    retry_count: int

    # === Execution Trace ===
    node_trace: Annotated[list[str], operator.add]