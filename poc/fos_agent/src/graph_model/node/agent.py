from graph_model.state.agentstate import AgentState
from utility.helper_func import logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from snowflake.cortex import complete
from utility.snowflake_session import session
import json

# ============================================================================
# NODE 1: AGENT NODE (LLM Call)
# ============================================================================

def agent_node(state: AgentState) -> AgentState:
    """
    Agent node: Makes LLM call to decide next action.
    Analyzes messages and determines which tool to call.
    """
    messages = state["messages"]
    iteration = state.get("iteration_count", 0) + 1
    
    logger.info(f"Executing agent node - Iteration: {iteration}")
    logger.debug(f"Number of messages in state: {len(messages)}")
    
    system_prompt = """You are a data assistant with access to the following tools:
   
    1. call_cortex_llm: Generate text using Cortex LLM
    - Args: prompt (str)

    2. cortex_analyst_query : Generate response using Cortex Analayst
    - Args: question (str)

    When you need to use a tool, respond with a JSON block:
    ```json
    {
        "tool": "tool_name",
        "args": {"arg1": "value1", "arg2": "value2"}
    }
    ```

    When you have gathered enough information to provide a final answer, respond with:
    ```json
    {
        "final_answer": "Your comprehensive response here"
    }
    ```

Always validate your outputs before providing final answers."""

    conversation = f"{system_prompt}\n\n"
    for msg in messages:
        if isinstance(msg, HumanMessage):
            conversation += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            conversation += f"Assistant: {msg.content}\n"
        elif isinstance(msg, ToolMessage):
            conversation += f"Tool Result ({msg.name}): {msg.content}\n"
    
    conversation += "Assistant:"
    
    logger.debug(f"Conversation context length: {len(conversation)} characters")
    
    try:
        logger.debug("Calling Mistral-large2 model for agent decision")
        response = complete(
            model="mistral-large2",
            prompt=conversation,
            session=session
        )
        logger.info(f"Agent LLM call successful - Response length: {len(str(response))}")
        logger.debug(f"Agent response: {str(response)[:300]}..." if len(str(response)) > 300 else f"Agent response: {response}")
    except Exception as e:
        logger.error(f"Error calling agent LLM: {str(e)}", exc_info=True)
        response = f"Error calling LLM: {str(e)}"
    
    tool_calls = []
    final_output = None
    
    logger.debug("Parsing agent response for tool calls or final answer")
    
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            
            if "tool" in parsed:
                tool_calls.append({
                    "id": f"call_{iteration}",
                    "name": parsed["tool"],
                    "args": parsed.get("args", {})
                })
                logger.info(f"Parsed tool call: {parsed['tool']}")
            elif "final_answer" in parsed:
                final_output = parsed["final_answer"]
                logger.info("Parsed final answer from agent")
        elif "{" in response and "}" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            parsed = json.loads(response[start:end])
            
            if "tool" in parsed:
                tool_calls.append({
                    "id": f"call_{iteration}",
                    "name": parsed["tool"],
                    "args": parsed.get("args", {})
                })
                logger.info(f"Parsed tool call: {parsed['tool']}")
            elif "final_answer" in parsed:
                final_output = parsed["final_answer"]
                logger.info("Parsed final answer from agent")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from agent response: {str(e)}")
        pass
    
    ai_message = AIMessage(content=response)
    
    logger.debug(f"Agent node complete - Tool calls: {len(tool_calls)}, Has final output: {bool(final_output)}")
    
    return {
        **state,
        "messages": messages + [ai_message],
        "tool_calls": tool_calls,
        "iteration_count": iteration,
        "final_output": final_output or state.get("final_output", "")
    }

