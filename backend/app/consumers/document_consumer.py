import asyncio
import json
import logging
import os
import re # Added import
import shutil
import sys
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
from app.llm_providers.prompt_factory import ChatPromptFactory # Added for Markdown conversion
from app.llm_providers.llm_factory import LLMFactory # Added for LLM client
from app.llm_providers.utils import clean_markdown_response # Added for cleaning LLM responses

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

def split_by_sentence(text, max_words=2000):
    # Split text into sentences (basic rule-based approach)
    sentences = re.findall(r'[^.!?]+[.!?]?', text.strip())
    
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence: # Skip empty sentences
            continue
        word_count = len(sentence.split())

        if current_word_count + word_count > max_words and current_chunk: # Ensure current_chunk is not empty before appending
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = word_count
        elif current_word_count + word_count <= max_words: # Only add if it fits
            current_chunk.append(sentence)
            current_word_count += word_count
        else: # Sentence itself is too long, add it as its own chunk
            if current_chunk: # Append previous chunk first
                 chunks.append(' '.join(current_chunk))
            chunks.append(sentence)
            current_chunk = []
            current_word_count = 0


    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

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
            # Step 1: Convert with MarkItDown
            logger.info(f"Attempting MarkItDown conversion for {doc_upload.file_name}.")
            md_converter = MarkItDown(enable_plugins=False) # Consider if plugins are needed
            conversion_result = md_converter.convert(temp_file_path)

            if conversion_result and conversion_result.markdown and conversion_result.markdown.strip():
                markdown_from_markitdown = conversion_result.markdown
                logger.info(f"MarkItDown successfully converted {doc_upload.file_name} to initial markdown.")
            else:
                # If MarkItDown fails or returns empty, we might still try LLM with raw content if possible,
                # or handle as an error. For now, let's log and proceed, LLM might still work with raw.
                logger.warning(f"MarkItDown conversion failed or produced empty markdown for {doc_upload.file_name}.")
                markdown_from_markitdown = "" # Ensure it's an empty string

            # Step 2: Refine with LLM
            # The LLM will now try to refine the MarkItDown output, or convert raw if MarkItDown failed.
            # Determine content for LLM: MarkItDown output if available, otherwise raw file content.
            
            content_for_llm = markdown_from_markitdown
            if not content_for_llm.strip(): # If MarkItDown output was empty, try to read raw file content
                logger.info(f"MarkItDown output was empty for {doc_upload.file_name}. Reading raw file content for LLM.")
                try:
                    with open(temp_file_path, 'rb') as f:
                        raw_bytes = f.read()
                    try:
                        raw_content_for_llm = raw_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        logger.warning(f"UTF-8 decoding failed for {doc_upload.file_name} (LLM fallback). Trying latin-1.")
                        try:
                            raw_content_for_llm = raw_bytes.decode('latin-1')
                        except UnicodeDecodeError:
                            logger.error(f"Could not decode file content for {doc_upload.file_name} (LLM fallback) with utf-8 or latin-1.")
                            raw_content_for_llm = ""
                    content_for_llm = raw_content_for_llm
                except Exception as e_read:
                    logger.error(f"Error reading raw file content for LLM fallback for {doc_upload.file_name}: {e_read}")
                    content_for_llm = "" # Ensure it's empty if read fails

            final_markdown_content = ""
            if content_for_llm.strip():
                logger.info(f"Attempting LLM refinement/conversion for {doc_upload.file_name}.")
                to_markdown_prompt_str = ChatPromptFactory.to_markdown_prompt()
                client, model = LLMFactory.create_async_client('gemini')
                
                content_chunks = split_by_sentence(content_for_llm) # Split content
                processed_chunks = []

                for chunk_index, chunk in enumerate(content_chunks):
                    if not chunk.strip():
                        continue
                    logger.info(f"Processing chunk {chunk_index + 1}/{len(content_chunks)} for {doc_upload.file_name}")
                    completion_kwargs = {
                        "messages": [
                            {"role": "user", "content": chunk},
                            {"role": "developer", "content": to_markdown_prompt_str}
                        ],
                        "temperature": 0.5,
                        "model": model,
                    }
                    
                    try:
                        response = await client.chat.completions.create(**completion_kwargs)
                        if response and response.choices and response.choices[0].message and response.choices[0].message.content:
                            raw_content = response.choices[0].message.content
                            cleaned_content = clean_markdown_response(raw_content)
                            processed_chunks.append(cleaned_content)
                            logger.info(f"LLM successfully processed chunk {chunk_index + 1} for {doc_upload.file_name}.")
                        else:
                            logger.warning(f"LLM failed to process chunk {chunk_index + 1} for {doc_upload.file_name} or returned empty. Skipping this chunk.")
                    except Exception as e_llm_chunk:
                        logger.error(f"Error processing chunk {chunk_index + 1} with LLM for {doc_upload.file_name}: {e_llm_chunk}")
                        # Optionally, decide if you want to append the original chunk or skip
                        # For now, skipping if LLM fails for a chunk.

                if processed_chunks:
                    final_markdown_content = "\\n\\n".join(processed_chunks) # Join processed chunks
                    logger.info(f"LLM successfully refined/converted content for {doc_upload.file_name} to markdown from {len(content_chunks)} chunks.")
                else:
                    logger.warning(f"LLM failed to process any chunks for {doc_upload.file_name}. Using MarkItDown output if available.")
                    final_markdown_content = markdown_from_markitdown # Fallback to MarkItDown's direct output
            else:
                logger.warning(f"No content available (neither from MarkItDown nor raw file) for LLM processing for {doc_upload.file_name}. Markdown will be empty.")
                final_markdown_content = "" # Ensure it's empty

            markdown_content = final_markdown_content # Assign to the variable used later

            # Save the refined markdown to S3 (or local storage if S3 is not configured)
            if markdown_content.strip():
                markdown_file_name = f"{doc_upload.file_hash}.md"
                if s3_client and s3_bucket_name:
                    # Define a specific path for markdown files in S3
                    markdown_s3_path = f"markdowns/project_{doc_upload.project_id}/{doc_upload.file_hash}/{markdown_file_name}"
                    s3_client.put_object(
                        Bucket=s3_bucket_name,
                        Key=markdown_s3_path,
                        Body=markdown_content.encode('utf-8'),
                        ContentType='text/markdown'
                    )
                    document_record.markdown_s3_link = f"s3://{s3_bucket_name}/{markdown_s3_path}"
                    logger.info(f"Markdown for document {document_record.id} saved to S3: {document_record.markdown_s3_link}")
                else:
                    # Define a specific path for markdown files in local storage
                    perm_markdown_dir = os.path.join(os.getcwd(), "permanent_storage", "markdowns", f"project_{doc_upload.project_id}", doc_upload.file_hash)
                    os.makedirs(perm_markdown_dir, exist_ok=True)
                    perm_markdown_path = os.path.join(perm_markdown_dir, markdown_file_name)
                    with open(perm_markdown_path, "w", encoding="utf-8") as md_file:
                        md_file.write(markdown_content)
                    document_record.markdown_s3_link = perm_markdown_path
                    logger.info(f"Markdown for document {document_record.id} saved locally: {document_record.markdown_s3_link}")
                db.commit()
            
            logger.info(f"Successfully processed markdown conversion for {doc_upload.file_name} for upload {upload_id}")
            
        except Exception as e:
            db.rollback()  # Rollback any potential partial commit
            logger.error(f"Error during markdown conversion or saving for upload {upload_id}: {e}", exc_info=True)
            await _update_upload_status(db, upload_id, "error", f"Markdown conversion/saving failed: {e}", document_id=document_record.id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            db.close()
            return  # Stop further processing for this message

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
