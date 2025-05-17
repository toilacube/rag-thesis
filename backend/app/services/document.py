import os
import hashlib
import shutil
import boto3
import logging
from fastapi import Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional, Dict, Tuple
from datetime import UTC, datetime
import uuid
import json # For RabbitMQ message

from app.models.models import Document, DocumentUpload, Project, DocumentChunk
from app.config.config import getConfig
from db.database import get_db_session
from app.services.rabbitmq import RabbitMQService, get_rabbitmq_service # Import RabbitMQService

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # DOCX
    "application/msword", # DOC
    "text/plain", # TXT
    "text/markdown", # MD
    "application/vnd.ms-excel", # XLS
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # XLSX
]
MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB
TEMP_DIR = os.path.join(os.getcwd(), "temp")

def create_temp_file_path(filename: str) -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(TEMP_DIR, unique_filename)

class DocumentService:
    def __init__(
        self, 
        db: Session = Depends(get_db_session),
        rabbitmq_service: RabbitMQService = Depends(get_rabbitmq_service)
        ):
        self.db = db
        self.config = getConfig()
        self.rabbitmq_service = rabbitmq_service
        self.s3_client = self._create_s3_client()
        self.bucket_name = self.config.MINIO_BUCKET_NAME if self.s3_client else None
        
    def _create_s3_client(self): # This S3 client is for the synchronous part of upload if needed
        try:
            # This client might not be strictly needed here if all S3 ops are in consumer
            # But keeping it in case of future needs for DocumentService
            endpoint_url = self.config.MINIO_ENDPOINT
            access_key = self.config.MINIO_ACCESS_KEY
            secret_key = self.config.MINIO_SECRET_KEY
            
            if not all([endpoint_url, access_key, secret_key, self.config.MINIO_BUCKET_NAME]):
                logger.warning("MinIO not fully configured. S3 client for DocumentService not initialized.")
                return None
                
            s3_client = boto3.client(
                's3', endpoint_url=endpoint_url,
                aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                region_name='us-east-1', config=boto3.session.Config(signature_version='s3v4')
            )
            try:
                s3_client.head_bucket(Bucket=self.config.MINIO_BUCKET_NAME)
                logger.info(f"S3 Bucket '{self.config.MINIO_BUCKET_NAME}' accessible by DocumentService.")
            except Exception:
                logger.warning(f"S3 Bucket '{self.config.MINIO_BUCKET_NAME}' not found or inaccessible by DocumentService. Attempting to create.")
                try:
                    s3_client.create_bucket(Bucket=self.config.MINIO_BUCKET_NAME)
                    logger.info(f"S3 Bucket '{self.config.MINIO_BUCKET_NAME}' created by DocumentService.")
                except Exception as create_e:
                    logger.error(f"Failed to create S3 bucket '{self.config.MINIO_BUCKET_NAME}' by DocumentService: {create_e}")
                    return None
            return s3_client
        except Exception as e:
            logger.error(f"Error initializing S3 client in DocumentService: {e}")
            return None

    async def upload_documents(
        self, 
        files: List[UploadFile], 
        project_id: int, 
        user_id: int
    ) -> List[Dict]: # Returns List[DocumentUploadResult]
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID {project_id} not found")
        
        upload_results = []
        
        for file in files:
            file_result = {"file_name": file.filename, "status": "error", "upload_id": None, "document_id": None, "is_exist": False, "error": None}
            try:
                if file.content_type not in ALLOWED_CONTENT_TYPES:
                    file_result["error"] = f"Unsupported file type: {file.content_type}"
                    logger.warning(f"Unsupported file type for {file.filename}: {file.content_type}")
                    upload_results.append(file_result)
                    continue
                
                content = await file.read()
                file_size = len(content)
                await file.seek(0)
                
                if file_size == 0:
                    file_result["error"] = "File is empty."
                    logger.warning(f"Empty file uploaded: {file.filename}")
                    upload_results.append(file_result)
                    continue

                if file_size > MAX_FILE_SIZE:
                    file_result["error"] = f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)"
                    logger.warning(f"File size exceeded for {file.filename}: {file_size} bytes")
                    upload_results.append(file_result)
                    continue
                
                file_hash = hashlib.sha256(content).hexdigest()
                
                existing_document = self.db.query(Document).filter(
                    Document.project_id == project_id,
                    Document.file_hash == file_hash
                ).first()
                
                if existing_document:
                    file_result["status"] = "exists"
                    file_result["document_id"] = existing_document.id
                    file_result["is_exist"] = True
                    logger.info(f"Document {file.filename} (hash: {file_hash}) already exists in project {project_id}.")
                    upload_results.append(file_result)
                    continue
                
                temp_file_path = create_temp_file_path(file.filename)
                try:
                    with open(temp_file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                except Exception as e:
                    file_result["error"] = f"Error saving temporary file: {e}"
                    logger.error(f"Error saving temp file {file.filename}: {e}", exc_info=True)
                    upload_results.append(file_result)
                    continue
                
                now = datetime.now(UTC)
                document_upload = DocumentUpload(
                    project_id=project_id,
                    file_name=file.filename, 
                    file_hash=file_hash,
                    file_size=file_size,
                    content_type=file.content_type,
                    temp_path=temp_file_path,
                    user_id=user_id,
                    status="queued", # Initial status before RabbitMQ pickup
                    created_at=now,
                    updated_at=now
                )
                
                self.db.add(document_upload)
                self.db.commit()
                self.db.refresh(document_upload)

                # Publish message to RabbitMQ
                message_body = {"document_upload_id": document_upload.id}
                published = self.rabbitmq_service.publish_message(
                    queue_name=self.config.RABBITMQ_DOCUMENT_QUEUE,
                    message=message_body
                )

                if published:
                    file_result["status"] = "queued"
                    file_result["upload_id"] = document_upload.id
                    logger.info(f"File {file.filename} (upload_id: {document_upload.id}) queued for processing via RabbitMQ.")
                else:
                    # Rollback DocumentUpload creation or mark as error if MQ publish fails
                    document_upload.status = "error"
                    document_upload.error_message = "Failed to queue for processing."
                    self.db.commit()
                    file_result["status"] = "error"
                    file_result["upload_id"] = document_upload.id
                    file_result["error"] = "Failed to queue for processing."
                    logger.error(f"Failed to publish message to RabbitMQ for DocumentUpload {document_upload.id}.")
                
                upload_results.append(file_result)
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error during upload of file '{getattr(file, 'filename', 'unknown')}': {e}", exc_info=True)
                self.db.rollback()
                file_result["error"] = f"Unexpected server error: {e}"
                upload_results.append(file_result)
            finally:
                if hasattr(file, 'file') and file.file:
                     file.file.close()
        return upload_results
    
    async def get_documents_with_status(self, project_id: int) -> List[Dict]:
        # Retrieve all DocumentUpload entries for the project
        uploads_and_docs = self.db.query(
                DocumentUpload, 
                Document
            ).outerjoin(Document, DocumentUpload.document_id == Document.id)\
            .filter(DocumentUpload.project_id == project_id)\
            .all()

        results = []
        for upload, doc in uploads_and_docs:
            status_detail = {
                "id": doc.id if doc else None, # Document ID
                "file_path": doc.file_path if doc else None,
                "file_name": upload.file_name, # Use upload's filename as it's the source
                "file_size": doc.file_size if doc else upload.file_size,
                "content_type": doc.content_type if doc else upload.content_type,
                "file_hash": doc.file_hash if doc else upload.file_hash,
                "project_id": upload.project_id,
                "created_at": doc.created_at if doc else upload.created_at, # Show doc creation time if available
                "updated_at": doc.updated_at if doc else upload.updated_at,
                "uploaded_by": upload.user_id,
                "processing_status": upload.status,
                "error_message": upload.error_message,
                "upload_id": upload.id,
            }
            # Refine processing_status
            if doc and upload.status == "completed":
                status_detail["processing_status"] = "completed"
            elif upload.status in ["queued", "processing"]:
                 status_detail["processing_status"] = upload.status
            elif upload.status == "error":
                status_detail["processing_status"] = "error"
            elif not doc and upload.status == "pending": # Should be queued
                status_detail["processing_status"] = "pending_queue" # Or just "pending"
            else: # Fallback or initial upload state
                status_detail["processing_status"] = upload.status

            results.append(status_detail)
        return results

class DocumentProcessingService: # Primarily for status checks now
    def __init__(self, db: Session = Depends(get_db_session)):
        self.db = db
        # S3 client or other processing dependencies are now mainly in the consumer
        # QdrantService is also used by consumer

    async def get_processing_status(self, upload_ids: List[int]) -> Dict[int, Dict]:
        result_map: Dict[int, Dict] = {}
        document_uploads = self.db.query(DocumentUpload).filter(
            DocumentUpload.id.in_(upload_ids)
        ).all()
        
        for upload_id_query in upload_ids: # Iterate through requested IDs to ensure all are covered
            doc_upload = next((du for du in document_uploads if du.id == upload_id_query), None)

            if not doc_upload:
                result_map[upload_id_query] = {"status": "not_found", "detail": "DocumentUpload ID not found."}
                continue
            
            status_info = {
                "upload_id": doc_upload.id,
                "file_name": doc_upload.file_name,
                "upload_status": doc_upload.status,
                "upload_error": doc_upload.error_message,
                "document_id": doc_upload.document_id # ID of the processed Document record
            }
            result_map[doc_upload.id] = status_info
            
        return result_map

def get_document_service(
    db: Session = Depends(get_db_session),
    rabbitmq_service: RabbitMQService = Depends(get_rabbitmq_service)
) -> DocumentService:
    return DocumentService(db=db, rabbitmq_service=rabbitmq_service)

def get_document_processing_service(
    db: Session = Depends(get_db_session)
) -> DocumentProcessingService:
    # QdrantService is not directly injected here anymore, consumer will get it.
    return DocumentProcessingService(db=db)