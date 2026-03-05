from langgraph.graph import StateGraph, END
from graph_model.state.agentstate import AgentState
from graph_model.node.tool import tool_node
from graph_model.node.agent import agent_node
from graph_model.node.validate import validate_node
from graph_model.router.routing_logic import route_after_agent, route_after_validate

def build_agent_graph() -> StateGraph:
    """Build the 3-node LangGraph agent."""
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("validate", validate_node)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tool": "tool",
            "validate": "validate",
            "end": END
        }
    )
    
    workflow.add_edge("tool", "agent")
    
    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "agent": "agent",
            "end": END
        }
    )
    
    return workflow.compile()