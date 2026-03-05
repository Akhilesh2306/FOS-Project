from langchain_core.tools import tool
from snowflake.cortex import complete
from utility.helper_func import logger
from utility.snowflake_session import session
import json

@tool
def call_cortex_llm(
    prompt: str,
    model: str = "mistral-large2",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """
    Calls Snowflake Cortex LLM for text generation.
    
    Args:
        prompt: The prompt to send to the LLM
        model: Model name (mistral-large2, llama3.1-70b, etc.)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated text from the LLM
    """
    logger.info(f"Calling Cortex LLM - Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}")
    logger.debug(f"Prompt: {prompt[:200]}..." if len(prompt) > 200 else f"Prompt: {prompt}")
    
    try:
        response = complete(
            model=model,
            prompt=prompt,
            session=session,
            options={
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        
        logger.info(f"Cortex LLM call successful - Response length: {len(str(response))}")
        logger.debug(f"LLM Response: {str(response)[:200]}..." if len(str(response)) > 200 else f"LLM Response: {response}")
        
        return json.dumps({
            "status": "success",
            "model": model,
            "generated_text": response
        })
        
    except Exception as e:
        logger.error(f"Error calling Cortex LLM: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error": str(e),
            "model": model
        })
