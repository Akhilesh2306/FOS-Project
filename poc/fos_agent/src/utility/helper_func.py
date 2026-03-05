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


