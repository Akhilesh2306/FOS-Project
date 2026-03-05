from pub_sub_model.event_hub_config import logger
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
from azure.eventhub import EventData
from azure.eventhub.exceptions import EventHubError
from datetime import datetime
import json


# ============================================================================
# EVENT PUBLISHER (for testing)
# ============================================================================

class EventPublisher:
    """Helper class to publish test events to Event Hub"""
    
    @staticmethod
    def publish_event(event_data: dict):
        """Publish a single event to Event Hub"""
        try:
            producer = EventHubProducerClient.from_connection_string(
                EVENTHUB_CONNECTION_STRING,
                eventhub_name=EVENTHUB_NAME
            )
            
            with producer:
                event_batch = producer.create_batch()
                event_batch.add(EventData(json.dumps(event_data).encode('utf-8')))
                producer.send_batch(event_batch)
            
            logger.info(f"Published event: {event_data.get('event_id', 'unknown')}")
            logger.info("✅ Event sent successfully!")

        except EventHubError as e:
            logger.info(f"❌ Event Hub error: {e}")
        except Exception as e:
            logger.info(f"❌ General error: {e}")
        finally:
            # Always close the producer
            try:
                producer.close()
            except:
                pass
    
    @staticmethod
    def publish_test_events():
        """Publish sample test events"""
        test_events = [
            {
                "event_id": "evt_001",
                "event_type": "opportunity_inactivity",
                "timestamp": datetime.now().isoformat(),
                "source": "crm_system",
                "query": "What actions should we take?",
                "metadata": {"opp_id": "OPP-12345", "days_inactive": 10},
                "priority": "high"
            },
            {
                "event_id": "evt_002",
                "event_type": "competitor_alert",
                "timestamp": datetime.now().isoformat(),
                "source": "conversation_analysis",
                "query": "Competitor mentioned in recent call",
                "metadata": {"account_id": "ACC-67890", "competitor": "Competitor X"},
                "priority": "high"
            },
            {
                "event_id": "evt_003",
                "event_type": "data_query",
                "timestamp": datetime.now().isoformat(),
                "source": "user_request",
                "query": "Get top 10 opportunities by deal value",
                "metadata": {},
                "priority": "normal"
            }
        ]
        
        for event in test_events:
            EventPublisher.publish_event(event)
