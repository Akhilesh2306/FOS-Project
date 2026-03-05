from pydantic import BaseModel
from typing import Optional

# ============================================================================
# EVENT SCHEMA
# ============================================================================
class AgentTriggerEvent(BaseModel):
    """Schema for events that trigger the agent"""
    event_id: str
    event_type: str
    timestamp: str
    source: str
    query: str
    metadata: Optional[dict] = {}
    priority: str = "normal"
    callback_url: Optional[str] = None