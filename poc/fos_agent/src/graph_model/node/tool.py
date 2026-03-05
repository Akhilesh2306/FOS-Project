from graph_model.state.agentstate import AgentState
from utility.helper_func import logger
from graph_model.agent_tools.register_tool import tool_map
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import json
# ============================================================================
# NODE 2: TOOL NODE (Tool Execution)
# ============================================================================

def tool_node(state: AgentState) -> AgentState:
    """
    Tool node: Executes the tool calls from agent node.
    """
    tool_calls = state.get("tool_calls", [])
    messages = state["messages"]
    tool_results = state.get("tool_results", [])
    
    logger.info(f"Executing tool node - {len(tool_calls)} tool call(s) to process")
    
    for call in tool_calls:
        tool_name = call["name"]
        tool_args = call["args"]
        call_id = call["id"]
        
        logger.info(f"Processing tool call: {tool_name} (ID: {call_id})")
        logger.info(f"Tool arguments: {tool_args}")
        
        if tool_name in tool_map:
            try:
                tool_fn = tool_map[tool_name]
                logger.info(f"Invoking tool function: {tool_name}")
                result = tool_fn.invoke(tool_args)
                
                logger.info(f"Tool {tool_name} executed successfully")
                
                tool_results.append({
                    "call_id": call_id,
                    "tool": tool_name,
                    "status": "success",
                    "result": result
                })
                
                messages.append(ToolMessage(
                    content=result,
                    name=tool_name,
                    tool_call_id=call_id
                ))
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
                error_result = json.dumps({
                    "status": "error",
                    "tool": tool_name,
                    "error": str(e)
                })
                
                tool_results.append({
                    "call_id": call_id,
                    "tool": tool_name,
                    "status": "error",
                    "result": error_result
                })
                
                messages.append(ToolMessage(
                    content=error_result,
                    name=tool_name,
                    tool_call_id=call_id
                ))
        else:
            logger.warning(f"Unknown tool requested: {tool_name}")
            error_result = json.dumps({
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(tool_map.keys())
            })
            
            tool_results.append({
                "call_id": call_id,
                "tool": tool_name,
                "status": "error",
                "result": error_result
            })
            
            messages.append(ToolMessage(
                content=error_result,
                name=tool_name,
                tool_call_id=call_id
            ))
    
    logger.info(f"Tool node complete - Processed {len(tool_calls)} tool call(s)")
    
    return {
        **state,
        "messages": messages,
        "tool_calls": [],
        "tool_results": tool_results
    }
