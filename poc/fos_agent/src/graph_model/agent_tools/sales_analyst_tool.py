from langchain_core.tools import tool
from utility.snowflake_session import session
from utility.helper_func import logger
import requests
from typing import Dict, Any
import json

# ============================================
# CORTEX ANALYST TOOL
# ============================================

def _get_cortex_analyst_response(question: str, semantic_view: str) -> dict:
    """
    Call Cortex Analyst REST API to get SQL from natural language.
    """
    # Get connection details from the active session
    account = session.get_current_account()
    token = session._conn._rest._token
    
    # Build the REST API URL
    host = f"https://{account}.snowflakecomputing.com"
    url = f"{host}/api/v2/cortex/analyst/message"

    logger.info(f"Preparing to call Cortex Analyst API - Host: {host})")
    
    headers = {
        "Authorization": f"Snowflake Token=\"{token}\"",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ],
        "semantic_view": semantic_view
    }

    logger.info(f"Calling Cortex Analyst API - URL: {url}, Semantic View: {semantic_view}")
    logger.info(f"Request payload: {json.dumps(payload)}")
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


@tool
def cortex_analyst_query(question: str, semantic_model: str = "FOS_SF_DB.DATA.SFDC_SALES_ANALYST") -> str:
    """
    Query data using Cortex Analyst with natural language.
    Converts questions to SQL using the semantic model.
    
    Args:
        question: Natural language question about the data
        semantic_model: Fully qualified semantic model name (semantic view)
    """
    try:
        logger.info(f"Executing Cortex Analyst query - Semantic Model: {semantic_model}, Question: {question}")
        
        # Call Cortex Analyst REST API
        response = _get_cortex_analyst_response(question, semantic_model)
        logger.info(f"Cortex Analyst response: {response}")
        
        # Parse the response content
        content = response.get("message", {}).get("content", [])
        sql_statement = None
        explanation = ""
        
        for item in content:
            if item.get("type") == "sql":
                sql_statement = item.get("statement")
            elif item.get("type") == "text":
                explanation = item.get("text", "")
        
        if sql_statement:
            # Execute the generated SQL
            data = session.sql(sql_statement).to_pandas()
            return json.dumps({
                "status": "success",
                "sql": sql_statement,
                "explanation": explanation,
                "data": data.to_dict(orient='records')[:50]  # Limit rows
            }, default=str)
        else:
            return json.dumps({
                "status": "success", 
                "response": response
            })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})