"""Environment configuration for FOS agents"""

# Import external libraries
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """
    Configuration for BaseFOSAgent and all tools.
    """

    model_config = SettingsConfigDict(
        env_prefix="FOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_agent_settings() -> AgentSettings:
    """ 
    Cached singleton function - avoids parsing env vars on every call.
    """
    return AgentSettings()
