from langchain_core.tools import tool
from utility.snowflake_session import session
from utility.helper_func import logger
import json

# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@tool
def query_semantic_view(
    view_name: str,
    query: str,
    limit: int = 100
) -> str:
    """
    Executes a query against a Semantic layer view via Snowpark SDK.
    Returns rows as a list of dicts.
    
    Args:
        view_name: Fully qualified view name (e.g., 'FOS_PROD.SEMANTIC.SALES_VIEW')
        query: SQL query to execute against the view (use {view} as placeholder)
        limit: Maximum number of rows to return (default: 100)
    
    Returns:
        JSON string containing rows as list of dicts
    """
    logger.info(f"Executing query_semantic_view - View: {view_name}, Limit: {limit}")
    logger.debug(f"Query: {query}")
    
    try:
        if "{view}" in query:
            sql = query.replace("{view}", view_name)
        else:
            sql = f"SELECT * FROM {view_name} WHERE {query} LIMIT {limit}" if query else f"SELECT * FROM {view_name} LIMIT {limit}"
        
        logger.debug(f"Generated SQL: {sql}")
        df = session.sql(sql).to_pandas()
        logger.info(f"Query executed successfully - Retrieved {len(df)} rows")
        
        result = {
            "status": "success",
            "row_count": len(df),
            "columns": list(df.columns),
            "data": df.head(limit).to_dict(orient='records')
        }
        return json.dumps(result, default=str)
        
    except Exception as e:
        logger.error(f"Error executing query_semantic_view: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error": str(e),
            "view_name": view_name,
            "query": query
        })
