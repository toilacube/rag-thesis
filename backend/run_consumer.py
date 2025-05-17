import logging
import os
import sys

# Add project root to Python path
# This ensures that imports like 'from app.consumers.document_consumer import start_consumer' work
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir # If run_consumer.py is in the backend/ root
# If run_consumer.py is in, for example, backend/app/, adjust accordingly:
# project_root = os.path.abspath(os.path.join(current_dir, '..')) 

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.consumers.document_consumer import start_consumer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting RabbitMQ document consumer...")
    try:
        start_consumer()
    except Exception as e:
        logger.critical(f"Consumer failed to start or crashed: {e}", exc_info=True)
        sys.exit(1) # Exit with error code if consumer cannot start