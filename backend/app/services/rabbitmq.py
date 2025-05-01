import json
import pika
from typing import Dict, Any, Optional
from app.config.config import getConfig
import logging

logger = logging.getLogger(__name__)

class RabbitMQService:
    """Service for interacting with RabbitMQ message queues."""
    
    def __init__(self):
        """Initialize the RabbitMQ service with configuration."""
        self.config = getConfig()
        self.connection = None
        self.channel = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Establish connection to RabbitMQ server."""
        try:
            # Set up connection parameters
            credentials = pika.PlainCredentials(
                self.config.RABBITMQ_USER,
                self.config.RABBITMQ_PASSWORD
            )
            
            connection_params = pika.ConnectionParameters(
                host=self.config.RABBITMQ_HOST,
                port=self.config.RABBITMQ_PORT,
                virtual_host=self.config.RABBITMQ_VHOST,
                credentials=credentials
            )
            
            # Create connection and channel
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declare queues to ensure they exist
            self.channel.queue_declare(queue=self.config.RABBITMQ_DOCUMENT_QUEUE, durable=True)
            self.channel.queue_declare(queue=self.config.RABBITMQ_CHUNK_QUEUE, durable=True)
            
            logger.info("Successfully connected to RabbitMQ server")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self.connection = None
            self.channel = None
    
    def publish_message(self, queue_name: str, message: Dict[str, Any], 
                        correlation_id: Optional[str] = None) -> bool:
        """
        Publish a message to the specified queue.
        
        Args:
            queue_name: Name of the queue to publish to
            message: Dictionary containing message data
            correlation_id: Optional correlation ID for message tracking
            
        Returns:
            bool: True if message was published successfully, False otherwise
        """
        if not self.connection or self.connection.is_closed:
            self._initialize_connection()
            
        if not self.channel:
            logger.error("No RabbitMQ channel available")
            return False
            
        try:
            # Convert message to JSON
            message_body = json.dumps(message).encode('utf-8')
            
            # Set up message properties
            properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json',
                correlation_id=correlation_id
            )
            
            # Publish message
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_body,
                properties=properties
            )
            
            logger.info(f"Published message to queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False
    
    def close_connection(self):
        """Close the RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

# Singleton instance
_rabbitmq_service = None

def get_rabbitmq_service() -> RabbitMQService:
    """Get the RabbitMQ service singleton instance."""
    global _rabbitmq_service
    if _rabbitmq_service is None:
        _rabbitmq_service = RabbitMQService()
    return _rabbitmq_service