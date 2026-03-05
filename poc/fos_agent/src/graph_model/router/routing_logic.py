from typing import Literal
from graph_model.state.agentstate import AgentState
from utility.helper_func import logger

# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_agent(state: AgentState) -> Literal["tool", "validate", "end"]:
    """Route after agent node based on tool calls and final output."""
    tool_calls = state.get("tool_calls", [])
    final_output = state.get("final_output", "")
    iteration = state.get("iteration_count", 0)
    
    logger.info(f"Routing after agent - Iteration: {iteration}, Tool calls: {len(tool_calls)}, Has final output: {bool(final_output)}")
    
    if iteration >= 5:
        logger.warning("Maximum iterations (10) reached - routing to end")
        return "end"
    
    if tool_calls:
        logger.info("Routing to tool node")
        return "tool"
    
    if final_output:
        logger.info("Routing to validate node")
        return "validate"
    
    logger.info("No tool calls or final output - routing to validate")
    return "validate"


def route_after_validate(state: AgentState) -> Literal["agent", "end"]:
    """Route after validation based on validation status."""
    validation_status = state.get("validation_status", "pending")
    iteration = state.get("iteration_count", 0)
    
    logger.info(f"Routing after validate - Status: {validation_status}, Iteration: {iteration}")
    
    if validation_status == "valid":
        logger.info("Validation successful - routing to end")
        return "end"
    elif validation_status == "retry" and iteration < 5:
        logger.info("Validation requesting retry - routing back to agent")
        return "agent"
    else:
        logger.info("Validation failed or max retries reached - routing to end")
        return "end"