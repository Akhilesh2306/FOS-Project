import os
import logging
from dotenv import load_dotenv

"""Load environment variables from a .env file."""
load_dotenv(override=True)  # Load environment variables from .env file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='FOS_AGENT: %(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Azure Event Hub imports
try:
    from azure.eventhub.aio import EventHubConsumerClient, EventHubProducerClient
    from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
    AZURE_EVENTHUB_AVAILABLE = True
except ImportError:
    AZURE_EVENTHUB_AVAILABLE = False
    logger.info("Azure Event Hub SDK not installed. Run: pip install azure-eventhub azure-eventhub-checkpointstoreblob-aio")

try:
    # ============================================================================
    # AZURE EVENT HUB CONFIGURATION
    # ============================================================================
    EVENTHUB_CONNECTION_STRING = os.getenv("AZURE_EVENTHUB_CONNECTION_STRING")
    EVENTHUB_NAME = os.getenv("AZURE_EVENTHUB_NAME")
    EVENTHUB_CONSUMER_GROUP = os.getenv("AZURE_EVENTHUB_CONSUMER_GROUP")
    BLOB_STORAGE_CONNECTION_STRING = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
    BLOB_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME")

    if not all([EVENTHUB_CONNECTION_STRING, EVENTHUB_NAME, EVENTHUB_CONSUMER_GROUP, BLOB_STORAGE_CONNECTION_STRING, BLOB_CONTAINER_NAME]):
        logger.warning("One or more Azure Event Hub configuration variables are missing. Please check your .env file.")    
        raise ValueError("Missing Azure Event Hub configuration variables.") 

except Exception as e:
    logger.error(f"Error loading Azure Event Hub configuration: {e}")

