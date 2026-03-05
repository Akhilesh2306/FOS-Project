from utility.helper_func import logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from graph_model.state.agentstate import AgentState
from graph_model.graph_builder.agent_graph import build_agent_graph

# ============================================================================
# MAIN INTERFACE
# ============================================================================

class AgentRunner:
    """Runner class for the LangGraph agent."""
    
    def __init__(self):
        logger.info("Initializing AgentRunner")
        self.graph = build_agent_graph()
        logger.info("AgentRunner initialized successfully")
    
    def run(self, user_query: str) -> dict:
        """Execute the agent with a user query."""
        logger.info(f"Starting agent execution with query: {user_query}")
        
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_query)],
            "tool_calls": [],
            "tool_results": [],
            "validation_status": "pending",
            "validation_errors": [],
            "iteration_count": 0,
            "final_output": ""
        }
        
        try:
            logger.debug("Invoking agent graph")
            final_state = self.graph.invoke(initial_state)
            
            logger.info(f"Agent execution complete - Iterations: {final_state.get('iteration_count', 0)}, "
                       f"Validation: {final_state.get('validation_status', 'unknown')}")
            
            return {
                "query": user_query,
                "final_output": final_state.get("final_output", ""),
                "validation_status": final_state.get("validation_status", ""),
                "validation_errors": final_state.get("validation_errors", []),
                "iterations": final_state.get("iteration_count", 0),
                "tool_results": final_state.get("tool_results", [])
            }
        except Exception as e:
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            raise
    
    def stream(self, user_query: str):
        """Stream the agent execution for real-time updates."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_query)],
            "tool_calls": [],
            "tool_results": [],
            "validation_status": "pending",
            "validation_errors": [],
            "iteration_count": 0,
            "final_output": ""
        }
        
        for event in self.graph.stream(initial_state):
            yield event