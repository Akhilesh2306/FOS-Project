from typing import TypedDict, Literal, Annotated, Any
class AgentState(TypedDict):
    messages: list
    tool_calls: list
    tool_results: list
    validation_status: str
    validation_errors: list
    iteration_count: int
    final_output: str
