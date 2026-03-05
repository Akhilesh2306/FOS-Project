from graph_model.state.agentstate import AgentState
from utility.helper_func import logger
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# ============================================================================
# NODE 3: VALIDATE NODE (Output Validation)
# ============================================================================

def validate_node(state: AgentState) -> AgentState:
    """
    Validate node: Validates the output before returning to user.
    Checks for completeness, accuracy, and format.
    """
    messages = state["messages"]
    tool_results = state.get("tool_results", [])
    final_output = state.get("final_output", "")
    
    logger.info("Executing validation node")
    logger.debug(f"Validating final output: {bool(final_output)}, Tool results: {len(tool_results)}")
    
    validation_errors = []
    validation_status = "pending"
    
    for result in tool_results:
        if result.get("status") == "error":
            validation_errors.append(f"Tool error in {result.get('tool')}: {result.get('result')}")
            logger.warning(f"Validation found tool error: {result.get('tool')}")
    
    if final_output:
        if len(final_output) < 10:
            validation_errors.append("Final output too short - may be incomplete")
            logger.warning("Validation: Final output is too short")
        
        if any(phrase in final_output.lower() for phrase in ["i don't know", "unable to", "cannot"]):
            validation_errors.append("Output indicates uncertainty - may need retry")
            logger.warning("Validation: Output indicates uncertainty")
        
        try:
            if final_output.strip().startswith("{"):
                json.loads(final_output)
        except json.JSONDecodeError:
            pass
    
    recent_errors = sum(1 for r in tool_results[-3:] if r.get("status") == "error")
    if recent_errors >= 2:
        validation_errors.append("Multiple recent tool failures detected")
        logger.warning(f"Validation: {recent_errors} recent tool failures detected")
    
    if not validation_errors:
        validation_status = "valid"
        logger.info("Validation passed - Status: valid")
    elif len(validation_errors) <= 2 and state.get("iteration_count", 0) < 5:
        validation_status = "retry"
        logger.info(f"Validation requesting retry - Errors: {len(validation_errors)}")
    else:
        validation_status = "failed"
        logger.warning(f"Validation failed - Errors: {validation_errors}")
    
    if validation_status == "retry" and validation_errors:
        retry_message = HumanMessage(
            content=f"Validation found issues: {'; '.join(validation_errors)}. Please retry or provide a corrected response."
        )
        messages = messages + [retry_message]
        logger.debug("Added retry message to conversation")
    
    return {
        **state,
        "messages": messages,
        "validation_status": validation_status,
        "validation_errors": validation_errors
    }
