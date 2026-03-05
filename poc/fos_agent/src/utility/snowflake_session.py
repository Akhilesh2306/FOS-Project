import os
from utility.helper_func import logger
from snowflake.snowpark import Session

# ============================================================================
# SNOWFLAKE SESSION
# ============================================================================
def get_snowflake_session() -> Session:
    """Create Snowflake session from environment or OAuth token (SPCS) """
    logger.info("Creating Snowflake session")
    try:
        token_path = "/snowflake/session/token"
        
        if os.path.exists(token_path):
            session = Session.builder.configs({
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "host": os.getenv("SNOWFLAKE_HOST"),
                "authenticator": "oauth",
                "token": open(token_path).read(),
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE")
            }).create()
        else:
            session = Session.builder.configs({
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "role": os.getenv("SNOWFLAKE_ROLE"),
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE")
            }).create()

        logger.info(f"Snowflake session created successfully - Database: {os.getenv('SNOWFLAKE_DATABASE')}, Schema: {os.getenv('SNOWFLAKE_SCHEMA')}")
        return session
    except Exception as e:
        logger.error(f"Failed to create Snowflake session: {str(e)}", exc_info=True)
        raise

session=get_snowflake_session()