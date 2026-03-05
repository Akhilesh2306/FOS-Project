from graph_model.agent_run import AgentRunner
from pub_sub_model.event_schema import AgentTriggerEvent
from datetime import datetime
from utility.helper_func import logger
from utility.snowflake_session import session
from pub_sub_model.event_hub_config import (
    AZURE_EVENTHUB_AVAILABLE,
    EVENTHUB_CONNECTION_STRING,
    EVENTHUB_NAME,
    EVENTHUB_CONSUMER_GROUP,
    BLOB_STORAGE_CONNECTION_STRING,
    BLOB_CONTAINER_NAME,
    EventHubConsumerClient,
    EventHubProducerClient,
    BlobCheckpointStore
)
from typing import Optional
import asyncio

# ============================================================================
# AZURE EVENT HUB CONSUMER - EVENT TRIGGERED AGENT
# ============================================================================

class EventHubAgentTrigger:
    """
    Event Hub consumer that triggers the LangGraph agent based on incoming events.
    """
    
    def __init__(self):
        self.agent = AgentRunner()
        self.processed_events = []
        self.consumer_client = None
        
        if not AZURE_EVENTHUB_AVAILABLE:
            raise ImportError("Azure Event Hub SDK not installed")
        
        logger.info("EventHubAgentTrigger initialized")
    
    def _parse_event(self, event_data: dict) -> Optional[AgentTriggerEvent]:
        """Parse incoming event data into AgentTriggerEvent schema"""
        try:
            return AgentTriggerEvent(
                event_id=event_data.get("event_id", str(datetime.now().timestamp())),
                event_type=event_data.get("event_type", "query"),
                timestamp=event_data.get("timestamp", datetime.now().isoformat()),
                source=event_data.get("source", "eventhub"),
                query=event_data.get("query", ""),
                metadata=event_data.get("metadata", {}),
                priority=event_data.get("priority", "normal"),
                callback_url=event_data.get("callback_url")
            )
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None
    
    def _build_query_from_event(self, event: AgentTriggerEvent) -> str:
        """Build agent query from event data"""
        base_query = event.query
        
        if event.event_type == "opportunity_inactivity":
            base_query = f"Analyze opportunity {event.metadata.get('opp_id', 'unknown')} for inactivity and suggest next best actions. {base_query}"
        elif event.event_type == "competitor_alert":
            base_query = f"Check competitor mentions for account {event.metadata.get('account_id', 'unknown')} and recommend response strategy. {base_query}"
        elif event.event_type == "deal_stage_change":
            base_query = f"Deal stage changed for opportunity {event.metadata.get('opp_id', 'unknown')}. Analyze and suggest actions. {base_query}"
        elif event.event_type == "data_query":
            pass
        
        return base_query
    
    async def process_event(self, event) -> dict:
        """Process a single event and trigger the agent"""
        try:
            event_body = event.body_as_json()
            logger.info(f"Received event: {event_body.get('event_id', 'unknown')}")
            
            parsed_event = self._parse_event(event_body)
            if not parsed_event:
                return {"status": "error", "error": "Failed to parse event"}
            
            query = self._build_query_from_event(parsed_event)
            logger.info(f"Triggering agent with query: {query[:100]}...")
            
            result = self.agent.run(query)
            
            response = {
                "status": "success",
                "event_id": parsed_event.event_id,
                "event_type": parsed_event.event_type,
                "agent_result": result,
                "processed_at": datetime.now().isoformat()
            }
            
            self._log_result_to_snowflake(parsed_event, result)
            
            self.processed_events.append(response)
            logger.info(f"Event {parsed_event.event_id} processed successfully")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return {"status": "error", "error": str(e)}
    
    def _log_result_to_snowflake(self, event: AgentTriggerEvent, result: dict):
        """Log the agent result to Snowflake for audit"""
        try:
            database_name = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
            logger.info(f"Logging result to Snowflake database: {database_name}")
            schema_name = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
            logger.info(f"Logging result to Snowflake schema: {schema_name}")
            log_data = {
                "EVENT_ID": event.event_id,
                "EVENT_TYPE": event.event_type,
                "EVENT_SOURCE": event.source,
                "QUERY": event.query,
                "AGENT_OUTPUT": result.get("final_output", ""),
                "VALIDATION_STATUS": result.get("validation_status", ""),
                "ITERATIONS": result.get("iterations", 0),
                "PROCESSED_AT": datetime.now().isoformat()
            }
            
            cols = ", ".join(log_data.keys())
            vals = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in log_data.values()])
            
            session.sql(f"""
                INSERT INTO {database_name}.{schema_name}.AGENT_EVENT_LOG ({cols}) VALUES ({vals})
            """).collect()
            
            logger.info(f"Logged result for event {event.event_id} to Snowflake")
            
        except Exception as e:
            logger.warning(f"Failed to log to Snowflake: {e}")
    
    async def on_event(self, partition_context, event):
        """Event handler callback for Event Hub consumer"""
        result = await self.process_event(event)
        
        await partition_context.update_checkpoint(event)
        
        return result
    
    async def on_error(self, partition_context, error):
        """Error handler for Event Hub consumer"""
        logger.error(f"Error in partition {partition_context.partition_id}: {error}")
    
    def start_consumer(self):
        """Start the Event Hub consumer (blocking)"""
        logger.info("Starting Event Hub consumer...")
        
        if BLOB_STORAGE_CONNECTION_STRING:
            checkpoint_store = BlobCheckpointStore.from_connection_string(
                BLOB_STORAGE_CONNECTION_STRING,
                BLOB_CONTAINER_NAME
            )
            
            self.consumer_client = EventHubConsumerClient.from_connection_string(
                EVENTHUB_CONNECTION_STRING,
                consumer_group=EVENTHUB_CONSUMER_GROUP,
                eventhub_name=EVENTHUB_NAME,
                checkpoint_store=checkpoint_store
            )
        else:
            self.consumer_client = EventHubConsumerClient.from_connection_string(
                EVENTHUB_CONNECTION_STRING,
                consumer_group=EVENTHUB_CONSUMER_GROUP,
                eventhub_name=EVENTHUB_NAME
            )
        
        logger.info(f"Connected to Event Hub: {EVENTHUB_NAME}")
        
        with self.consumer_client:
            self.consumer_client.receive(
                on_event=lambda pc, e: asyncio.run(self.on_event(pc, e)),
                on_error=lambda pc, e: asyncio.run(self.on_error(pc, e)),
                starting_position="-1"
            )
    
    async def start_consumer_async(self):
        """Start the Event Hub consumer (async)"""
        logger.info("Starting Event Hub consumer (async)...")
        
        if BLOB_STORAGE_CONNECTION_STRING:
            checkpoint_store = BlobCheckpointStore.from_connection_string(
                BLOB_STORAGE_CONNECTION_STRING,
                BLOB_CONTAINER_NAME
            )
            
            self.consumer_client = EventHubConsumerClient.from_connection_string(
                EVENTHUB_CONNECTION_STRING,
                consumer_group=EVENTHUB_CONSUMER_GROUP,
                eventhub_name=EVENTHUB_NAME,
                checkpoint_store=checkpoint_store
            )
        else:
            self.consumer_client = EventHubConsumerClient.from_connection_string(
                EVENTHUB_CONNECTION_STRING,
                consumer_group=EVENTHUB_CONSUMER_GROUP,
                eventhub_name=EVENTHUB_NAME
            )
        
        async with self.consumer_client:
            await self.consumer_client.receive(
                on_event=self.on_event,
                on_error=self.on_error,
                starting_position="-1"
            )
    
    def stop_consumer(self):
        """Stop the Event Hub consumer"""
        if self.consumer_client:
            self.consumer_client.close()
            logger.info("Event Hub consumer stopped")
