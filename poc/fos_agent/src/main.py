from graph_model.agent_tools.register_tool import tool_map
from graph_model.state.agentstate import AgentState
from pub_sub_model.agent_trigger import EventHubAgentTrigger
from utility.helper_func import logger
from utility.snowflake_session import get_snowflake_session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from utility.snowflake_session import session
from graph_model.agent_run import AgentRunner
from snowflake.cortex import complete
from pub_sub_model.publisher import EventPublisher

def main():

    logger.info("Starting FOS Agent - Event Hub Integration")

    # logger.info("Publishing test events to Event Hub")
    # EventPublisher.publish_test_events()

    logger.info("Starting Event Hub consumer to trigger agent on incoming events")
    trigger = EventHubAgentTrigger()
    trigger.start_consumer()

    # ============================================================================
    # EXAMPLE USAGE
    # ============================================================================
    # logger.info("Starting LangGraph Agent Example")
    
    # agent = AgentRunner()
    
    # # queries = [
    # #     "Query the sales semantic view to get top 10 customers by revenue",
    # #     "Generate a summary of Q4 performance using Cortex LLM",
    # #     "Log an action item to the hybrid table for follow-up"
    # # ]

    # queries = [
    #     # "How to determine the next best actions for a deal?",
    #     "Give information about Acme Corp deal and suggest next steps",
    # ]
    
    # for query in queries:
    #     print(f"\n{'='*60}")
    #     print(f"Query: {query}")
    #     print('='*60)
        
    #     try:
    #         result = agent.run(query)
            
    #         print(f"Final Output: {result['final_output']}")
    #         print(f"Validation: {result['validation_status']}")
    #         print(f"Iterations: {result['iterations']}")
    #         if result['validation_errors']:
    #             print(f"Errors: {result['validation_errors']}")
    #     except Exception as e:
    #         logger.error(f"Failed to execute query: {str(e)}", exc_info=True)
    #         print(f"Error: {str(e)}")
    
    # logger.info("LangGraph Agent Example completed")

if __name__ == "__main__":
    main()
