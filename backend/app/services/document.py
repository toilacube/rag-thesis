import os
import hashlib
import shutil
import boto3
import asyncio
import logging # Added logging
from fastapi import Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict
from datetime import UTC, datetime
import uuid

from app.models.models import Document, DocumentUpload, ProcessingTask, Project, DocumentChunk # Added DocumentChunk
from app.config.config import getConfig
from db.database import get_db_session
import tempfile
from markitdown import MarkItDown
from app.services.chunking import chunk_markdown, save_chunks_to_database
from app.services.qdrant_service import QdrantService, get_qdrant_service # Added QdrantService
from qdrant_client import models as qdrant_models # Added Qdrant models

logger = logging.getLogger(__name__) # Added logger

# Define allowed file types and maximum file size
ALLOWED_CONTENT_TYPES = [
    "application/pdf",                  # PDF
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/msword",               # DOC
    "text/plain",                       # TXT
    "text/markdown",                    # MD
    "application/vnd.ms-excel",         # XLS
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # XLSX
]

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024
SUPPORTED_EXTENSIONS = ["docx", "pptx", "pdf", "xlsx", "txt", "md"] # Added txt, md
MAX_FILE_SIZE_MB = 50
MAX_FILE_NAME_LENGTH = 255 # Increased, as 50 might be too short for some file names

# Default MinIO configuration (handled by config now)

# Central temp directory
TEMP_DIR = os.path.join(os.getcwd(), "temp") # Make sure this aligns with docker-compose volume if used

def create_temp_file_path(filename):
    os.makedirs(TEMP_DIR, exist_ok=True)
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(TEMP_DIR, unique_filename)

class DocumentService:
    def __init__(self, db: Session = Depends(get_db_session)):
        self.db = db
        self.config = getConfig()
        self.s3_client = self._create_s3_client()
        if self.s3_client: # Check if client was created successfully
             self.bucket_name = self.config.MINIO_BUCKET_NAME
        else:
            self.bucket_name = None # Or handle error appropriately
        
    def _create_s3_client(self):
        try:
            endpoint_url = self.config.MINIO_ENDPOINT
            access_key = self.config.MINIO_ACCESS_KEY
            secret_key = self.config.MINIO_SECRET_KEY
            
            if not endpoint_url or not access_key or not secret_key: # Check endpoint_url too
                logger.warning("MinIO credentials or endpoint not fully configured. S3 client will not be initialized.")
                # raise ValueError("MinIO credentials not configured") # Or log and continue without S3
                return None 
                
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='us-east-1',
                config=boto3.session.Config(signature_version='s3v4')
            )
            
            # Ensure bucket exists
            bucket_name_to_check = self.config.MINIO_BUCKET_NAME # Use the actual bucket name
            if not bucket_name_to_check:
                logger.error("MinIO bucket name not configured.")
                return None

            try:
                s3_client.head_bucket(Bucket=bucket_name_to_check)
                logger.info(f"S3 Bucket '{bucket_name_to_check}' found.")
            except Exception as e: # Catch more specific ClientError if possible
                logger.warning(f"S3 Bucket '{bucket_name_to_check}' not found or inaccessible, attempting to create: {e}")
                try:
                    s3_client.create_bucket(Bucket=bucket_name_to_check)
                    logger.info(f"S3 Bucket '{bucket_name_to_check}' created successfully.")
                except Exception as create_e:
                    logger.error(f"Failed to create S3 bucket '{bucket_name_to_check}': {create_e}")
                    return None # Fail if bucket cannot be ensured
            return s3_client
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            return None
    
    # _create_document and _create_processing_task are not used in this class,
    # they seem to be helper concepts for DocumentProcessingService.
    # Consider moving them if they are only used there or refactoring.

    async def upload_documents(
        self, 
        files: List[UploadFile], 
        project_id: int, 
        user_id: int
    ) -> List[Dict]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        upload_results = []
        
        for file in files:
            try:
                # Validate file type
                if file.content_type not in ALLOWED_CONTENT_TYPES:
                    upload_results.append({
                        "file_name": file.filename, "status": "error", 
                        "error": f"Unsupported file type: {file.content_type}",
                        "upload_id": None, "is_exist": False
                    })
                    logger.warning(f"Unsupported file type for {file.filename}: {file.content_type}")
                    continue
                
                # Read file content for size and hash
                await file.seek(0)
                content = await file.read()
                file_size = len(content)
                await file.seek(0) # Reset cursor for saving
                
                if file_size == 0:
                    upload_results.append({
                        "file_name": file.filename, "status": "error",
                        "error": "File is empty.",
                        "upload_id": None, "is_exist": False
                    })
                    logger.warning(f"Empty file uploaded: {file.filename}")
                    continue

                if file_size > MAX_FILE_SIZE:
                    upload_results.append({
                        "file_name": file.filename, "status": "error",
                        "error": f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)",
                        "upload_id": None, "is_exist": False
                    })
                    logger.warning(f"File size exceeded for {file.filename}: {file_size} bytes")
                    continue
                
                file_hash = hashlib.sha256(content).hexdigest()
                
                # Check for existing document with the same hash in the project
                existing_document = self.db.query(Document).filter(
                    Document.project_id == project_id,
                    Document.file_hash == file_hash
                ).first()
                
                if existing_document:
                    # Check if there's an existing DocumentUpload for this file that is pending/processing
                    # to avoid duplicate processing tasks.
                    existing_upload = self.db.query(DocumentUpload).filter(
                        DocumentUpload.project_id == project_id,
                        DocumentUpload.file_hash == file_hash,
                        DocumentUpload.status.in_(["pending", "processing"]) # Consider what "exists" means
                    ).first()

                    upload_id_for_existing = existing_upload.id if existing_upload else None
                    
                    upload_results.append({
                        "file_name": file.filename, "status": "exists",
                        "document_id": existing_document.id,
                        "upload_id": upload_id_for_existing, # May need reprocessing if requested
                        "is_exist": True
                    })
                    logger.info(f"Document {file.filename} (hash: {file_hash}) already exists in project {project_id}.")
                    continue
                
                # Save to a temporary location
                temp_file_path = create_temp_file_path(file.filename)
                try:
                    with open(temp_file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                except Exception as e:
                    upload_results.append({
                        "file_name": file.filename, "status": "error",
                        "error": f"Error saving temporary file: {str(e)}",
                        "upload_id": None, "is_exist": False
                    })
                    logger.error(f"Error saving temp file {file.filename}: {e}")
                    continue # Important: ensure file.file is reset or handled if loop continues with it
                finally:
                    await file.seek(0) # Ensure file pointer is reset for next iteration if any
                
                # Create DocumentUpload record
                document_upload = DocumentUpload(
                    project_id=project_id,
                    file_name=file.filename, 
                    file_hash=file_hash,
                    file_size=file_size,
                    content_type=file.content_type,
                    temp_path=temp_file_path, # Store temp path
                    user_id=user_id,
                    status="pending", # Initial status
                    created_at=datetime.now(UTC)
                )
                
                self.db.add(document_upload)
                self.db.commit()
                self.db.refresh(document_upload)
                
                upload_results.append({
                    "file_name": file.filename, "status": "pending",
                    "upload_id": document_upload.id, "is_exist": False
                })
                logger.info(f"File {file.filename} uploaded successfully (upload_id: {document_upload.id}), pending processing.")
                    
            except HTTPException: # Re-raise HTTPExceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error during upload of file '{getattr(file, 'filename', 'unknown')}': {e}", exc_info=True)
                self.db.rollback() # Rollback in case of partial commit for this file
                upload_results.append({
                    "file_name": getattr(file, 'filename', 'unknown'), "status": "error",
                    "error": f"Unexpected server error: {str(e)}",
                    "upload_id": None, "is_exist": False
                })
            finally:
                if hasattr(file, 'file') and file.file: # Close file object if it's an UploadFile
                     file.file.close()

        return upload_results
    
    async def get_documents_with_status(self, project_id: int):
        documents = self.db.query(Document).filter(Document.project_id == project_id).all()
        if not documents:
            return []
        
        document_ids = [doc.id for doc in documents]
        
        # Get the LATEST processing task for each document_id
        # This requires a more complex query if multiple tasks can exist per document.
        # Assuming one primary task for now, or the latest one based on created_at/updated_at.
        # For simplicity, let's grab all and then map.
        processing_tasks = self.db.query(ProcessingTask).filter(
            ProcessingTask.document_id.in_(document_ids)
        ).order_by(ProcessingTask.document_id, ProcessingTask.updated_at.desc()).all() # Get latest
        
        task_dict = {}
        for task in processing_tasks:
            if task.document_id not in task_dict: # Keep only the latest task
                 task_dict[task.document_id] = task
        
        result = []
        for document in documents:
            doc_dict = {
                "id": document.id, "file_path": document.file_path,
                "file_name": document.file_name, "file_size": document.file_size,
                "content_type": document.content_type, "file_hash": document.file_hash,
                "project_id": document.project_id, "created_at": document.created_at,
                "updated_at": document.updated_at, "uploaded_by": document.uploaded_by,
                "processing_status": "unknown", "error_message": None # Default status
            }
            
            task = task_dict.get(document.id)
            if task:
                doc_dict["processing_status"] = task.status
                doc_dict["error_message"] = task.error_message
            elif not self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).first():
                # If no task and no chunks, it might be an old document or processing failed before task creation
                doc_dict["processing_status"] = "pending_processing_or_failed_early"

            result.append(doc_dict)
            
        return result
    
    
class DocumentProcessingService:
    def __init__(
        self, 
        db: Session = Depends(get_db_session),
        qdrant_service: QdrantService = Depends(get_qdrant_service) # Inject QdrantService
        ):
        self.db = db
        self.config = getConfig()
        self.qdrant_service = qdrant_service # Store QdrantService
        self.s3_client = self._create_s3_client() # Re-use S3 client logic from DocumentService
        if self.s3_client:
            self.bucket_name = self.config.MINIO_BUCKET_NAME
        else:
            self.bucket_name = None


    # Copied _create_s3_client from DocumentService for consistency
    # In a larger app, this S3 client logic might be in its own service or utility
    def _create_s3_client(self):
        try:
            endpoint_url = self.config.MINIO_ENDPOINT
            access_key = self.config.MINIO_ACCESS_KEY
            secret_key = self.config.MINIO_SECRET_KEY
            
            if not endpoint_url or not access_key or not secret_key:
                logger.warning("MinIO credentials or endpoint not fully configured. S3 client will not be initialized for DocumentProcessingService.")
                return None
                
            s3_client = boto3.client(
                's3', endpoint_url=endpoint_url,
                aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                region_name='us-east-1', config=boto3.session.Config(signature_version='s3v4')
            )
            
            bucket_name_to_check = self.config.MINIO_BUCKET_NAME
            if not bucket_name_to_check:
                logger.error("MinIO bucket name not configured for DocumentProcessingService.")
                return None
            try:
                s3_client.head_bucket(Bucket=bucket_name_to_check)
            except:
                logger.warning(f"Bucket {bucket_name_to_check} not found by ProcessingService, attempting to create.")
                s3_client.create_bucket(Bucket=bucket_name_to_check)
            return s3_client
        except Exception as e:
            logger.error(f"Error initializing S3 client for DocumentProcessingService: {str(e)}")
            return None

    async def process_documents(self, upload_ids: List[int], user_id: int):
        document_uploads = self.db.query(DocumentUpload).filter(
            DocumentUpload.id.in_(upload_ids),
            DocumentUpload.status == "pending"
        ).all()
        
        if not document_uploads:
            logger.info(f"No pending document uploads found for IDs: {upload_ids}")
            return []

        tasks_created = []
        now = datetime.now(UTC)
        
        for doc_upload in document_uploads:
            # Check if a processing task already exists for this upload_id that isn't failed
            existing_task = self.db.query(ProcessingTask).filter(
                ProcessingTask.document_upload_id == doc_upload.id,
                ProcessingTask.status.notin_(['error']) # type: ignore 
            ).first()

            if existing_task:
                logger.info(f"Processing task {existing_task.id} already exists for upload {doc_upload.id} with status {existing_task.status}. Skipping task creation.")
                # Optionally, add to a list of "already processing" tasks
                continue

            task = ProcessingTask(
                project_id=doc_upload.project_id,
                status="pending", # Will be updated by the background task
                created_at=now,
                updated_at=now,
                document_upload_id=doc_upload.id,
                initiated_by=user_id
            )
            self.db.add(task)
            tasks_created.append(task)
        
        if tasks_created:
            self.db.commit()
            for task in tasks_created:
                self.db.refresh(task)
                logger.info(f"Created ProcessingTask {task.id} for DocumentUpload {task.document_upload_id}. Starting background processing.")
                # Update DocumentUpload status to 'queued' or 'processing_queued'
                doc_upload_obj = self.db.query(DocumentUpload).filter(DocumentUpload.id == task.document_upload_id).first()
                if doc_upload_obj:
                    doc_upload_obj.status = "queued" # A more descriptive status
                    self.db.commit()
                asyncio.create_task(self._process_document_pipeline(task.id))
        
        return tasks_created


    async def _update_task_status(self, db_session: Session, task_id: int, status: str, error_message: Optional[str] = None):
        """Safely updates task and related document upload status."""
        try:
            task = db_session.query(ProcessingTask).filter(ProcessingTask.id == task_id).first()
            if task:
                task.status = status
                task.updated_at = datetime.now(UTC)
                if error_message:
                    task.error_message = error_message
                
                doc_upload = db_session.query(DocumentUpload).filter(DocumentUpload.id == task.document_upload_id).first()
                if doc_upload:
                    doc_upload.status = status # Mirror status for simplicity, or have more granular DocumentUpload statuses
                    if error_message:
                         doc_upload.error_message = error_message
                db_session.commit()
                logger.info(f"Task {task_id} status updated to {status}.")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to update status for task {task_id}: {e}", exc_info=True)


    async def _process_document_pipeline(self, processing_task_id: int):
        """Full pipeline: file ops, text extraction, chunking, DB save, vector save."""
        # Create a new session for this background task
        db = next(get_db_session())
        document_record = None # To store the created Document record

        try:
            task = db.query(ProcessingTask).filter(ProcessingTask.id == processing_task_id).first()
            if not task:
                logger.error(f"Processing task {processing_task_id} not found in pipeline start.")
                return

            await self._update_task_status(db, processing_task_id, "processing_file")

            doc_upload = db.query(DocumentUpload).filter(DocumentUpload.id == task.document_upload_id).first()
            if not doc_upload:
                await self._update_task_status(db, processing_task_id, "error", "DocumentUpload record not found.")
                return

            logger.info(f"Starting file operations for task {processing_task_id}, upload {doc_upload.id}")

            # 1. Create Document record
            document_record = Document(
                file_path="", # Placeholder, updated after S3/local save
                file_name=doc_upload.file_name,
                file_size=doc_upload.file_size,
                content_type=doc_upload.content_type,
                file_hash=doc_upload.file_hash,
                project_id=doc_upload.project_id,
                uploaded_by=doc_upload.user_id, # Corrected: use user_id from doc_upload
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            db.add(document_record)
            db.commit()
            db.refresh(document_record)
            task.document_id = document_record.id # Link task to document
            db.commit()
            logger.info(f"Created Document record {document_record.id} for task {task.id}")

            # 2. Store file (S3 or local)
            temp_file_path = doc_upload.temp_path
            if not os.path.exists(temp_file_path):
                raise FileNotFoundError(f"Temporary file {temp_file_path} not found for task {task.id}.")

            if self.s3_client and self.bucket_name:
                s3_path = f"project_{doc_upload.project_id}/{doc_upload.file_hash}/{doc_upload.file_name}"
                with open(temp_file_path, "rb") as f:
                    self.s3_client.upload_fileobj(
                        f, self.bucket_name, s3_path,
                        ExtraArgs={"ContentType": doc_upload.content_type}
                    )
                document_record.file_path = f"s3://{self.bucket_name}/{s3_path}"
                logger.info(f"File for task {task.id} uploaded to S3: {document_record.file_path}")
            else:
                # Fallback to local storage if S3 not configured
                perm_dir = os.path.join(os.getcwd(), "permanent_storage", f"project_{doc_upload.project_id}", doc_upload.file_hash)
                os.makedirs(perm_dir, exist_ok=True)
                perm_path = os.path.join(perm_dir, doc_upload.file_name)
                shutil.copy2(temp_file_path, perm_path)
                document_record.file_path = perm_path # Relative or absolute path based on setup
                logger.info(f"File for task {task.id} saved locally: {document_record.file_path}")
            db.commit()

            # --- Content Processing, Chunking, Vectorization ---
            await self._update_task_status(db, processing_task_id, "processing_content")
            logger.info(f"Starting content processing for task {task.id}, document {document_record.id}")

            # 3. Convert document to Markdown
            # Using MarkItDown directly with the temp_file_path
            markdown_content = ""
            try:
                # Validate file extension for MarkItDown compatibility if necessary
                # For now, assume MarkItDown handles it or raises error
                md_converter = MarkItDown(enable_plugins=False) # Consider plugin needs
                conversion_result = md_converter.convert(temp_file_path)
                if not conversion_result or not conversion_result.markdown:
                    # Check for specific error messages from MarkItDown if available
                    raise Exception(f"MarkItDown conversion failed or produced no markdown for {doc_upload.file_name}.")
                markdown_content = conversion_result.markdown
                logger.info(f"Successfully converted {doc_upload.file_name} to markdown for task {task.id}")
            except Exception as e:
                logger.error(f"Error converting document to markdown for task {task.id}: {e}", exc_info=True)
                raise Exception(f"Markdown conversion error: {str(e)}") # Propagate to main try-except

            if not markdown_content.strip():
                logger.warning(f"Markdown content is empty for task {task.id}, document {document_record.id}. Skipping chunking and vectorization.")
                # This might be considered 'completed' if empty files are acceptable, or an 'error'/'warning' state.
                # For now, let's assume it's completed without chunks.
                await self._update_task_status(db, processing_task_id, "completed", "Document converted to empty markdown.")
            else:
                # 4. Chunk Markdown
                # chunk_markdown is from app.services.chunking
                # source_document for chunk_markdown should be document_record.id
                text_chunks = chunk_markdown(
                    markdown_text=markdown_content,
                    source_document=str(document_record.id) 
                    # Max_chunk_size, etc., use defaults or make configurable via task/project settings
                )
                logger.info(f"Generated {len(text_chunks)} chunks for task {task.id}")

                if not text_chunks:
                    logger.warning(f"No text chunks generated for task {task.id}, document {document_record.id}.")
                    # Similar to empty markdown, decide if this is 'completed' or an issue.
                    await self._update_task_status(db, processing_task_id, "completed", "No chunks generated from markdown.")
                else:
                    # 5. Save chunks to PostgreSQL
                    # save_chunks_to_database is from app.services.chunking
                    # It expects file_hash from the Document record (which is doc_upload.file_hash)
                    saved_chunk_db_ids = save_chunks_to_database(
                        db=db, # Pass the current session
                        chunks=text_chunks, # The output from chunk_markdown
                        document_id=document_record.id,
                        project_id=document_record.project_id,
                        file_name=document_record.file_name,
                        file_hash=document_record.file_hash
                    )
                    logger.info(f"Saved {len(saved_chunk_db_ids)} chunks to database for task {task.id}")

                    # 6. Generate embeddings and save to Qdrant
                    qdrant_points = []
                    # The `text_chunks` from `chunk_markdown` has the text and metadata.
                    # The `saved_chunk_db_ids` from `save_chunks_to_database` are the DocumentChunk.id values.
                    # We need to ensure these align or retrieve DocumentChunk objects to get their IDs.
                    # `save_chunks_to_database` uses chunk["metadata"]["chunk_id"] or generates one for DocumentChunk.id.
                    # Let's assume `chunk_markdown` sets a unique `chunk_id` in `chunk["metadata"]`
                    # that `save_chunks_to_database` uses as the primary key `DocumentChunk.id`.

                    chunk_texts_for_embedding = [chunk['text'] for chunk in text_chunks]
                    if chunk_texts_for_embedding:
                        embeddings = self.qdrant_service.get_embeddings(chunk_texts_for_embedding)
                        
                        for i, chunk_data in enumerate(text_chunks):
                            # Ensure chunk_id from metadata is the one used for DocumentChunk.id
                            # save_chunks_to_database uses chunk["metadata"].get("chunk_id") or generates one.
                            # It's safer to rely on the chunk_id in chunk_data["metadata"] if chunk_markdown sets it reliably.
                            # And this should be the same ID as `saved_chunk_db_ids[i]` if order is preserved.
                            # For robustness, it might be better if save_chunks_to_database returned List[DocumentChunk]
                            # or List[Dict[str, any]] with id and text.
                            # Given current save_chunks_to_database, we trust the `chunk_id` in metadata or index.
                            
                            # Let's use the chunk_id stored in chunk_data['metadata']['chunk_id']
                            # This ID is what `save_chunks_to_database` uses for `DocumentChunk.id`
                            qdrant_point_id = chunk_data["metadata"].get("chunk_id")
                            if not qdrant_point_id:
                                # This case should ideally not happen if chunk_markdown and save_chunks_to_database are robust
                                logger.error(f"Missing chunk_id in metadata for chunk {i} of document {document_record.id}. Skipping Qdrant upsert for this chunk.")
                                continue
                            
                            payload = {
                                "text": chunk_data["text"],
                                "document_id": document_record.id,
                                "project_id": document_record.project_id,
                                "file_name": document_record.file_name,
                                "chunk_metadata": chunk_data["metadata"], # Original metadata from chunk_markdown
                                "db_chunk_id": qdrant_point_id # Storing the DocumentChunk.id for reference
                            }
                            qdrant_points.append(qdrant_models.PointStruct(
                                id=qdrant_point_id, # Use the DocumentChunk.id as Qdrant point ID
                                vector=embeddings[i],
                                payload=payload
                            ))
                        
                        if qdrant_points:
                            self.qdrant_service.upsert_chunks(points=qdrant_points)
                            logger.info(f"Upserted {len(qdrant_points)} vectors to Qdrant for task {task.id}")
                        else:
                            logger.warning(f"No points to upsert to Qdrant for task {task.id} despite having text_chunks.")
                    else:
                        logger.warning(f"No chunk texts available for embedding for task {task.id}.")


                # 7. Final status update
                await self._update_task_status(db, processing_task_id, "completed")
                logger.info(f"Successfully completed processing pipeline for task {task.id}, document {document_record.id}")

            # 8. Clean up temporary file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {temp_file_path}: {e}")

        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError in processing pipeline for task {processing_task_id}: {e}", exc_info=True)
            await self._update_task_status(db, processing_task_id, "error", str(e))
        except Exception as e:
            logger.error(f"Error in processing pipeline for task {processing_task_id}: {e}", exc_info=True)
            # Ensure error status is set with a clear message
            error_detail = f"Pipeline failure: {type(e).__name__} - {str(e)}"
            await self._update_task_status(db, processing_task_id, "error", error_detail)
        finally:
            db.close()
            logger.info(f"Closed DB session for task {processing_task_id}")

    # This method is part of the old flow, not directly used by the new pipeline.
    # It can be kept for other uses or removed if _process_document_pipeline covers all needs.
    # For now, I am commenting it out as the new pipeline is more comprehensive.
    # async def process_markdown_and_save_chunks( ... )

    async def get_processing_status(self, upload_ids: List[int]) -> Dict:
        result = {}
        document_uploads = self.db.query(DocumentUpload).filter(
            DocumentUpload.id.in_(upload_ids)
        ).all()
        upload_dict = {upload.id: upload for upload in document_uploads}
        
        processing_tasks = self.db.query(ProcessingTask).filter(
            ProcessingTask.document_upload_id.in_(upload_ids)
        ).order_by(ProcessingTask.document_upload_id, ProcessingTask.updated_at.desc()).all() # Get latest
        
        task_dict_by_upload_id = {}
        for task in processing_tasks:
            if task.document_upload_id not in task_dict_by_upload_id:
                task_dict_by_upload_id[task.document_upload_id] = task
        
        for upload_id in upload_ids:
            doc_upload = upload_dict.get(upload_id)
            if not doc_upload:
                result[upload_id] = {"status": "not_found", "detail": "DocumentUpload ID not found."}
                continue
            
            task = task_dict_by_upload_id.get(upload_id)
            status_info = {
                "upload_id": doc_upload.id,
                "file_name": doc_upload.file_name,
                "upload_status": doc_upload.status, # Status from DocumentUpload
                "upload_error": doc_upload.error_message,
                "task_id": None,
                "task_status": None,
                "task_error": None,
                "document_id": None
            }
            
            if task:
                status_info["task_id"] = task.id
                status_info["task_status"] = task.status
                status_info["task_error"] = task.error_message
                status_info["document_id"] = task.document_id
            
            result[upload_id] = status_info
            
        return result
    
    # validate_file and document_to_markdown are not directly used in the new pipeline flow above.
    # Conversion is now handled within _process_document_pipeline using MarkItDown directly.
    # These can be kept as utilities if needed elsewhere.
    
    # def validate_file(self, file: UploadFile): # Added self, or make static
    #     file_extension = file.filename.split(".")[-1].lower()
    #     if file_extension not in SUPPORTED_EXTENSIONS:
    #         raise HTTPException(status_code=400, detail=f"Unsupported file type: .{file_extension}")

    #     file.file.seek(0, os.SEEK_END)
    #     file_size_mb = file.file.tell() / (1024 * 1024)
    #     file.file.seek(0)
    #     if file_size_mb > MAX_FILE_SIZE_MB:
    #         raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.")

    #     if len(file.filename) > MAX_FILE_NAME_LENGTH:
    #         # This modification of file.filename might not persist outside this call
    #         # It's better to handle filename length at the point of saving or record creation
    #         logger.warning(f"Filename '{file.filename}' exceeds max length {MAX_FILE_NAME_LENGTH}. It might be truncated by DB or OS.")
    #         # file.filename = file.filename[:MAX_FILE_NAME_LENGTH - len(file_extension) -1] + "." + file_extension # A safer truncation

    # async def document_to_markdown(self, file: UploadFile) -> str:
    #     # This method takes UploadFile. The pipeline uses file paths.
    #     # Consider adapting or creating a path-based version if this utility is needed.
    #     try:
    #         self.validate_file(file) # Call as instance method or make validate_file static
    #         temp_file_path = create_temp_file_path(file.filename)
    #         try:
    #             with open(temp_file_path, "wb") as buffer:
    #                 shutil.copyfileobj(file.file, buffer) # Use shutil for UploadFile content
                
    #             md = MarkItDown(enable_plugins=False) 
    #             result = md.convert(temp_file_path)
    #             if not result or not result.markdown:
    #                 raise Exception("Markdown conversion failed or produced empty content.")
    #             return result.markdown
    #         finally:
    #             if os.path.exists(temp_file_path):
    #                 os.remove(temp_file_path)
    #     except Exception as e:
    #         logger.error(f"Error in document_to_markdown for {file.filename}: {e}", exc_info=True)
    #         raise HTTPException(status_code=500, detail=f"Failed to convert document to markdown: {str(e)}")


def get_document_service(db: Session = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db)

def get_document_processing_service(
    db: Session = Depends(get_db_session),
    qdrant_service: QdrantService = Depends(get_qdrant_service) # Inject QdrantService here
) -> DocumentProcessingService:
    return DocumentProcessingService(db=db, qdrant_service=qdrant_service)