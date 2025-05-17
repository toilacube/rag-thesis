import asyncio
import json
import logging
import os
import shutil
import time # For retries
from datetime import UTC, datetime
from typing import Optional

import boto3
from qdrant_client import models as qdrant_models
from sqlalchemy.orm import Session

from app.config.config import getConfig
from app.models.models import Document, DocumentUpload, DocumentChunk # DocumentChunk for type hinting
from db.database import SessionLocal # Use SessionLocal to create new sessions
from app.services.chunking import chunk_markdown, save_chunks_to_database
from app.services.qdrant_service import QdrantService # Import, don't use get_qdrant_service directly in global scope
from app.services.rabbitmq import RabbitMQService # For type hinting, actual instance created locally
from markitdown import MarkItDown # Assuming this is the correct import

# Configure logging for the consumer
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# S3 Client Initialization (similar to services, but scoped to consumer needs)
def _create_s3_client_for_consumer(config_obj):
    try:
        endpoint_url = config_obj.MINIO_ENDPOINT
        access_key = config_obj.MINIO_ACCESS_KEY
        secret_key = config_obj.MINIO_SECRET_KEY
        bucket_name = config_obj.MINIO_BUCKET_NAME

        if not all([endpoint_url, access_key, secret_key, bucket_name]):
            logger.warning("MinIO not fully configured for consumer. S3 operations will fail.")
            return None, None
            
        s3_client = boto3.client(
            's3', endpoint_url=endpoint_url,
            aws_access_key_id=access_key, aws_secret_access_key=secret_key,
            region_name='us-east-1', config=boto3.session.Config(signature_version='s3v4')
        )
        # Ensure bucket exists (optional, could rely on prior creation)
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except Exception:
            logger.info(f"S3 Bucket '{bucket_name}' not found by consumer, attempting to create.")
            s3_client.create_bucket(Bucket=bucket_name)
        return s3_client, bucket_name
    except Exception as e:
        logger.error(f"Error initializing S3 client for consumer: {e}")
        return None, None

async def _update_upload_status(db_session: Session, upload_id: int, status: str, error_message: Optional[str] = None, document_id: Optional[int] = None):
    """Safely updates DocumentUpload status and associated document_id if provided."""
    try:
        doc_upload = db_session.query(DocumentUpload).filter(DocumentUpload.id == upload_id).first()
        if doc_upload:
            doc_upload.status = status
            doc_upload.updated_at = datetime.now(UTC)
            if error_message:
                doc_upload.error_message = error_message
            if document_id:
                doc_upload.document_id = document_id
            db_session.commit()
            logger.info(f"DocumentUpload {upload_id} status updated to {status}. Document ID: {document_id if document_id else 'N/A'}")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to update status for DocumentUpload {upload_id}: {e}", exc_info=True)


async def process_message_callback(ch, method, properties, body, qdrant_service_instance: QdrantService, s3_client, s3_bucket_name, app_config):
    """
    Callback function to process a message from RabbitMQ.
    Contains the core document processing pipeline.
    """
    logger.info(f"Received message: {body.decode()[:100]}...")
    db: Session = SessionLocal() # Create a new session for this message
    message_data = None
    upload_id = None

    try:
        message_data = json.loads(body.decode())
        upload_id = message_data.get("document_upload_id")

        if not upload_id:
            logger.error("Message missing 'document_upload_id'. Discarding.")
            ch.basic_ack(delivery_tag=method.delivery_tag) # Acknowledge to remove from queue
            return

        await _update_upload_status(db, upload_id, "processing")

        doc_upload = db.query(DocumentUpload).filter(DocumentUpload.id == upload_id).first()
        if not doc_upload:
            logger.error(f"DocumentUpload record {upload_id} not found. Discarding message.")
            await _update_upload_status(db, upload_id, "error", "Upload record not found during processing.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(f"Starting processing for DocumentUpload {upload_id}, file: {doc_upload.file_name}")

        # 1. Create Document record
        document_record = Document(
            file_path="", # Placeholder, updated after S3/local save
            file_name=doc_upload.file_name,
            file_size=doc_upload.file_size,
            content_type=doc_upload.content_type,
            file_hash=doc_upload.file_hash,
            project_id=doc_upload.project_id,
            uploaded_by=doc_upload.user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        db.add(document_record)
        db.commit()
        db.refresh(document_record)
        # Link DocumentUpload to the new Document record
        await _update_upload_status(db, upload_id, "processing", document_id=document_record.id)
        logger.info(f"Created Document record {document_record.id} for upload {upload_id}")

        # 2. Store file (S3 or local)
        temp_file_path = doc_upload.temp_path
        if not os.path.exists(temp_file_path):
            raise FileNotFoundError(f"Temporary file {temp_file_path} not found for upload {upload_id}.")

        if s3_client and s3_bucket_name:
            s3_path = f"project_{doc_upload.project_id}/{doc_upload.file_hash}/{doc_upload.file_name}"
            with open(temp_file_path, "rb") as f:
                s3_client.upload_fileobj(
                    f, s3_bucket_name, s3_path,
                    ExtraArgs={"ContentType": doc_upload.content_type}
                )
            document_record.file_path = f"s3://{s3_bucket_name}/{s3_path}"
            logger.info(f"File for upload {upload_id} uploaded to S3: {document_record.file_path}")
        else:
            perm_dir = os.path.join(os.getcwd(), "permanent_storage", f"project_{doc_upload.project_id}", doc_upload.file_hash)
            os.makedirs(perm_dir, exist_ok=True)
            perm_path = os.path.join(perm_dir, doc_upload.file_name)
            shutil.copy2(temp_file_path, perm_path)
            document_record.file_path = perm_path
            logger.info(f"File for upload {upload_id} saved locally: {document_record.file_path}")
        db.commit()

        # 3. Convert document to Markdown
        markdown_content = ""
        try:
            md_converter = MarkItDown(enable_plugins=False)
            conversion_result = md_converter.convert(temp_file_path)
            if not conversion_result or not conversion_result.markdown:
                raise Exception(f"MarkItDown conversion failed or produced no markdown for {doc_upload.file_name}.")
            markdown_content = conversion_result.markdown
            logger.info(f"Successfully converted {doc_upload.file_name} to markdown for upload {upload_id}")
        except Exception as e:
            logger.error(f"Error converting document to markdown for upload {upload_id}: {e}", exc_info=True)
            raise Exception(f"Markdown conversion error: {e}")

        if not markdown_content.strip():
            logger.warning(f"Markdown content is empty for upload {upload_id}, document {document_record.id}. Skipping chunking.")
            await _update_upload_status(db, upload_id, "completed", "Document converted to empty markdown.", document_id=document_record.id)
        else:
            # 4. Chunk Markdown
            text_chunks = chunk_markdown(
                markdown_text=markdown_content,
                source_document=str(document_record.id) 
            )
            logger.info(f"Generated {len(text_chunks)} chunks for document {document_record.id}")

            if not text_chunks:
                logger.warning(f"No text chunks generated for document {document_record.id}.")
                await _update_upload_status(db, upload_id, "completed", "No chunks generated from markdown.", document_id=document_record.id)
            else:
                # 5. Save chunks to PostgreSQL
                saved_chunk_db_ids = save_chunks_to_database(
                    db=db, chunks=text_chunks, document_id=document_record.id,
                    project_id=document_record.project_id, file_name=document_record.file_name,
                    file_hash=document_record.file_hash
                )
                logger.info(f"Saved {len(saved_chunk_db_ids)} chunks to database for document {document_record.id}")

                # 6. Generate embeddings and save to Qdrant
                qdrant_points = []
                chunk_texts_for_embedding = [chunk['text'] for chunk in text_chunks]
                if chunk_texts_for_embedding:
                    embeddings = qdrant_service_instance.get_embeddings(chunk_texts_for_embedding)
                    
                    for i, chunk_data in enumerate(text_chunks):
                        qdrant_point_id = chunk_data["metadata"].get("chunk_id")
                        if not qdrant_point_id:
                            logger.error(f"Missing chunk_id in metadata for chunk {i} of document {document_record.id}.")
                            continue
                        
                        payload = {
                            "text": chunk_data["text"], "document_id": document_record.id,
                            "project_id": document_record.project_id, "file_name": document_record.file_name,
                            "chunk_metadata": chunk_data["metadata"], "db_chunk_id": qdrant_point_id
                        }
                        qdrant_points.append(qdrant_models.PointStruct(
                            id=qdrant_point_id, vector=embeddings[i], payload=payload
                        ))
                    
                    if qdrant_points:
                        qdrant_service_instance.upsert_chunks(points=qdrant_points)
                        logger.info(f"Upserted {len(qdrant_points)} vectors to Qdrant for document {document_record.id}")

                await _update_upload_status(db, upload_id, "completed", document_id=document_record.id)
                logger.info(f"Successfully completed processing for DocumentUpload {upload_id}, Document {document_record.id}")

        # 7. Clean up temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file {temp_file_path}: {e}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError in processing for upload {upload_id}: {e}", exc_info=True)
        if upload_id: await _update_upload_status(db, upload_id, "error", str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Do not requeue on file not found
    except Exception as e:
        logger.error(f"Error processing message for upload {upload_id}: {e}", exc_info=True)
        error_detail = f"Processing pipeline failure: {type(e).__name__} - {str(e)}"
        if upload_id: await _update_upload_status(db, upload_id, "error", error_detail)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Requeue strategy depends on error type
    finally:
        if db:
            db.close()

def start_consumer():
    app_config = getConfig()
    
    # Initialize services needed by the consumer
    qdrant_service_instance = QdrantService(settings=app_config)
    s3_client, s3_bucket_name = _create_s3_client_for_consumer(app_config)

    if not qdrant_service_instance.client or not qdrant_service_instance.embedding_model:
        logger.critical("Qdrant service or embedding model failed to initialize. Consumer cannot start.")
        return

    # Initialize RabbitMQService connection
    # The RabbitMQService class itself handles connection and channel setup
    # We need to pass a lambda that captures the initialized services
    consumer_rabbitmq_service = RabbitMQService() # Create a new instance for the consumer
    if not consumer_rabbitmq_service.channel:
        logger.critical("RabbitMQ connection failed for consumer. Consumer cannot start.")
        return

    queue_name = app_config.RABBITMQ_DOCUMENT_QUEUE
    consumer_rabbitmq_service.channel.queue_declare(queue=queue_name, durable=True)
    
    # Create a partial function or lambda for the callback
    # This ensures qdrant_service, s3_client, etc. are available in the callback's scope
    # Note: pika's `basic_consume` callback is not async directly.
    # The `process_message_callback` is async, so it needs to be run in an event loop.
    # This part is tricky with pika's blocking nature.
    # A common pattern is to run asyncio.run within the synchronous pika callback.

    def sync_callback_wrapper(ch, method, properties, body):
        asyncio.run(process_message_callback(ch, method, properties, body, qdrant_service_instance, s3_client, s3_bucket_name, app_config))

    consumer_rabbitmq_service.channel.basic_qos(prefetch_count=1) # Process one message at a time
    consumer_rabbitmq_service.channel.basic_consume(
        queue=queue_name,
        on_message_callback=sync_callback_wrapper
        # auto_ack=False # Manual ack is handled in process_message_callback
    )

    logger.info(f"[*] Waiting for messages in queue '{queue_name}'. To exit press CTRL+C")
    try:
        consumer_rabbitmq_service.channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer stopped.")
    except Exception as e:
        logger.error(f"Consumer crashed: {e}", exc_info=True)
    finally:
        if consumer_rabbitmq_service.connection and not consumer_rabbitmq_service.connection.is_closed:
            consumer_rabbitmq_service.connection.close()
        logger.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    # This allows running the consumer directly for testing,
    # but for production, use the run_consumer.py script.
    # Need to ensure PYTHONPATH is set correctly if running this file directly.
    # Example: PYTHONPATH=. python app/consumers/document_consumer.py
    logger.info("Attempting to start consumer directly from document_consumer.py")
    # Patch sys.path if running directly for imports to work from project root
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    start_consumer()