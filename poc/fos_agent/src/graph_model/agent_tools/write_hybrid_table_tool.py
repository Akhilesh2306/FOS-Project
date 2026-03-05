from langchain_core.tools import tool
from utility.snowflake_session import session
from utility.helper_func import logger   
import json

@tool
def write_hybrid_table(
    table_name: str,
    data: dict,
    operation: str = "INSERT"
) -> str:
    """
    Inserts or updates a row in a Hybrid Table via Snowpark SDK.
    
    Args:
        table_name: Fully qualified table name (e.g., 'FOS_PROD.GOLD.ACTIONS_LOG')
        data: Dictionary of column names and values to insert/update
        operation: 'INSERT', 'UPDATE', or 'UPSERT' (default: INSERT)
    
    Returns:
        Status of the operation
    """
    logger.info(f"Writing to hybrid table - Table: {table_name}, Operation: {operation}")
    logger.debug(f"Data: {data}")
    
    try:
        columns = list(data.keys())
        values = list(data.values())
        
        if operation.upper() == "INSERT":
            cols_str = ", ".join(columns)
            vals_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})"
            
        elif operation.upper() == "UPDATE":
            if "id" not in [c.lower() for c in columns]:
                return json.dumps({"status": "error", "error": "UPDATE requires 'id' column"})
            
            id_col = next(c for c in columns if c.lower() == "id")
            id_val = data[id_col]
            set_clause = ", ".join([
                f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
                for k, v in data.items() if k.lower() != "id"
            ])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_col} = '{id_val}'"
            
        elif operation.upper() == "UPSERT":
            cols_str = ", ".join(columns)
            vals_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
            update_clause = ", ".join([
                f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
                for k, v in data.items()
            ])
            sql = f"""
                MERGE INTO {table_name} t
                USING (SELECT {vals_str}) s
                ON t.id = s.id
                WHEN MATCHED THEN UPDATE SET {update_clause}
                WHEN NOT MATCHED THEN INSERT ({cols_str}) VALUES ({vals_str})
            """
        else:
            return json.dumps({"status": "error", "error": f"Unknown operation: {operation}"})
        
        logger.debug(f"Generated SQL: {sql}")
        session.sql(sql).collect()
        logger.info(f"Hybrid table write successful - Operation: {operation}, Table: {table_name}")
        
        return json.dumps({
            "status": "success",
            "operation": operation,
            "table": table_name,
            "affected_columns": columns
        })
        
    except Exception as e:
        logger.error(f"Error writing to hybrid table: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error": str(e),
            "table": table_name,
            "operation": operation
        })
