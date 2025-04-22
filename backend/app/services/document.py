import os
import hashlib
import shutil
import boto3
import asyncio
from fastapi import Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict
from datetime import UTC, datetime

from app.models.models import Document, DocumentUpload, ProcessingTask, Project
from app.config.config import getConfig
from db.database import get_db_session
import tempfile
from markitdown import MarkItDown

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
SUPPORTED_EXTENSIONS = ["docx", "pptx", "pdf", "xlsx"]
MAX_FILE_SIZE_MB = 50
MAX_FILE_NAME_LENGTH = 50

class DocumentService:
    def __init__(self, db: Session = Depends(get_db_session)):
        self.db = db
        self.config = getConfig()
        self.s3_client = self._create_s3_client()
        self.bucket_name = os.environ.get("MINIO_BUCKET_NAME", "documents")
        
    def _create_s3_client(self):
        """Create and configure S3/MinIO client"""
        try:
            endpoint_url = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
            access_key = os.environ.get("MINIO_ACCESS_KEY")
            secret_key = os.environ.get("MINIO_SECRET_KEY")
            
            if not access_key or not secret_key:
                raise ValueError("MinIO credentials not configured")
                
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='us-east-1',  # Placeholder region for MinIO
                config=boto3.session.Config(signature_version='s3v4')
            )
            
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
            except:
                s3_client.create_bucket(Bucket=self.bucket_name)
                
            return s3_client
        except Exception as e:
            print(f"Error initializing S3 client: {str(e)}")
            return None
    
    def _create_document(self, file_path, file_name, file_size, content_type, file_hash, project_id, user_id):
        """Create a document record in the database"""
        document = Document(
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            file_hash=file_hash,
            project_id=project_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            uploaded_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def _create_processing_task(self, project_id, document_id, document_upload_id, user_id):
        """Create a processing task for the document"""
        processing_task = ProcessingTask(
            project_id=project_id,
            document_id=document_id,
            status="pending",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            document_upload_id=document_upload_id,
            initiated_by=user_id
        )
        
        self.db.add(processing_task)
        self.db.commit()
        self.db.refresh(processing_task)
        return processing_task
    
    async def upload_documents(
        self, 
        files: List[UploadFile], 
        project_id: int, 
        user_id: int
    ) -> List[Dict]:
        """
        Upload multiple documents, validating them and creating necessary database records.
        
        Args:
            files: List of files to upload
            project_id: ID of the project to associate the documents with
            user_id: ID of the user uploading the documents
            
        Returns:
            List[Dict]: List of upload results containing upload_id and is_exist status
            
        Raises:
            HTTPException: If validation fails or other errors occur
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        upload_results = []
        
        for file in files:
            try:
                if file.content_type not in ALLOWED_CONTENT_TYPES:
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error", 
                        "error": f"Unsupported file type: {file.content_type}",
                        "upload_id": None,
                        "is_exist": False
                    })
                    continue
                
                try:
                    await file.seek(0)
                    content = await file.read()
                    file_size = len(content)
                    
                    await file.seek(0)
                except Exception as e:
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"Error reading file: {str(e)}",
                        "upload_id": None,
                        "is_exist": False
                    })
                    continue
                
                if file_size > MAX_FILE_SIZE:
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)",
                        "upload_id": None,
                        "is_exist": False
                    })
                    continue
                
                file_hash = hashlib.sha256(content).hexdigest()
                
                existing_document = self.db.query(Document).filter(
                    Document.project_id == project_id,
                    Document.file_hash == file_hash
                ).first()
                
                if existing_document:
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "exists",
                        "document_id": existing_document.id,
                        "upload_id": None,
                        "is_exist": True
                    })
                    continue
                
                os.makedirs(f"project_{project_id}/temp", exist_ok=True)
                temp_file_path = f"project_{project_id}/temp/{file.filename}"
                
                try:
                    with open(temp_file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                except Exception as e:
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"Error saving file: {str(e)}",
                        "upload_id": None,
                        "is_exist": False
                    })
                    await file.seek(0)
                    continue
                finally:
                    await file.seek(0)
                
                document_upload = DocumentUpload(
                    project_id=project_id,
                    file_name=file.filename, 
                    file_hash=file_hash,
                    file_size=file_size,
                    content_type=file.content_type,
                    temp_path=temp_file_path,
                    user_id=user_id,
                    status="pending",
                    created_at=datetime.now(UTC)
                )
                
                try:
                    self.db.add(document_upload)
                    self.db.commit()
                    self.db.refresh(document_upload)
                    
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "pending",
                        "upload_id": document_upload.id,
                        "is_exist": False
                    })
                    
                except IntegrityError as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        
                    self.db.rollback()
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"Database error: {str(e)}",
                        "upload_id": None,
                        "is_exist": False
                    })
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        
                    self.db.rollback()
                    upload_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"Error creating document upload record: {str(e)}",
                        "upload_id": None,
                        "is_exist": False
                    })
                    
            except Exception as e:
                upload_results.append({
                    "file_name": file.filename if hasattr(file, "filename") else "unknown",
                    "status": "error",
                    "error": f"Unexpected error: {str(e)}",
                    "upload_id": None,
                    "is_exist": False
                })
                
        return upload_results
    
    async def get_documents_with_status(self, project_id: int):
        """
        Get all documents for a project with their processing status
        
        Args:
            project_id: ID of the project to get documents for
            
        Returns:
            List of documents with their processing status
        """
        # Query all documents for the project
        documents = self.db.query(Document).filter(Document.project_id == project_id).all()
        
        if not documents:
            return []
        
        document_ids = [doc.id for doc in documents]
        
        processing_tasks = self.db.query(ProcessingTask).filter(
            ProcessingTask.document_id.in_(document_ids)
        ).all()
        
        task_dict = {}
        for task in processing_tasks:
            if task.document_id:
                task_dict[task.document_id] = task
        
        result = []
        for document in documents:
            doc_dict = {
                "id": document.id,
                "file_path": document.file_path,
                "file_name": document.file_name,
                "file_size": document.file_size,
                "content_type": document.content_type,
                "file_hash": document.file_hash,
                "project_id": document.project_id,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "uploaded_by": document.uploaded_by,
                "processing_status": None,
                "error_message": None
            }
            
            # Add processing status if available
            if document.id in task_dict:
                task = task_dict[document.id]
                doc_dict["processing_status"] = task.status
                doc_dict["error_message"] = task.error_message
            
            result.append(doc_dict)
            
        return result
    
    
class DocumentProcessingService:
    def __init__(self, db: Session = Depends(get_db_session)):
        self.db = db
        self.config = getConfig()
        self.s3_client = self._create_s3_client()
        self.bucket_name = os.environ.get("MINIO_BUCKET_NAME", "documents")
        
    def _create_s3_client(self):
        """Create and configure S3/MinIO client"""
        try:
            endpoint_url = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
            access_key = os.environ.get("MINIO_ACCESS_KEY")
            secret_key = os.environ.get("MINIO_SECRET_KEY")
            
            if not access_key or not secret_key:
                raise ValueError("MinIO credentials not configured")
                
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='us-east-1',  # Placeholder region for MinIO
                config=boto3.session.Config(signature_version='s3v4')
            )
            
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
            except:
                s3_client.create_bucket(Bucket=self.bucket_name)
                
            return s3_client
        except Exception as e:
            print(f"Error initializing S3 client: {str(e)}")
            return None
    
    async def process_documents(self, upload_ids: List[int], user_id: int):
        """
        Process documents that have been uploaded
        
        Args:
            upload_ids: List of document upload IDs to process
            user_id: ID of the user initiating the processing
            
        Returns:
            List[ProcessingTask]: The created processing tasks
        """
        tasks = []
        
        document_uploads = self.db.query(DocumentUpload).filter(
            DocumentUpload.id.in_(upload_ids),
            DocumentUpload.status == "pending"  # Only process pending uploads
        ).all()
        
        upload_dict = {upload.id: upload for upload in document_uploads}
        
        for upload_id in upload_ids:
            document_upload = upload_dict.get(upload_id)
            
            if not document_upload:
                print(f"Document upload {upload_id} not found or not in pending status")
                continue
            
            processing_task = ProcessingTask(
                project_id=document_upload.project_id,
                status="pending",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                document_upload_id=document_upload.id,
                initiated_by=user_id
            )
            
            self.db.add(processing_task)
            self.db.commit()
            self.db.refresh(processing_task)
            
            asyncio.create_task(self._process_document(processing_task.id))
            
            tasks.append(processing_task)
            
        return tasks
    
    async def _process_document(self, processing_task_id: int):
        """
        Process a document in the background
        
        Args:
            processing_task_id: ID of the processing task to execute
        """
        db = next(get_db_session())
        
        try:
            processing_task = db.query(ProcessingTask).filter(
                ProcessingTask.id == processing_task_id
            ).first()
            
            if not processing_task:
                print(f"Processing task {processing_task_id} not found")
                return
            
            document_upload = db.query(DocumentUpload).filter(
                DocumentUpload.id == processing_task.document_upload_id
            ).first()
            
            if not document_upload:
                print(f"Document upload {processing_task.document_upload_id} not found")
                processing_task.status = "error"
                processing_task.error_message = "Document upload not found"
                processing_task.updated_at = datetime.now(UTC)
                db.commit()
                return
            
            processing_task.status = "processing"
            document_upload.status = "processing"
            db.commit()
            
            document = Document(
                file_path="",  # Will be updated later
                file_name=document_upload.file_name,
                file_size=document_upload.file_size,
                content_type=document_upload.content_type,
                file_hash=document_upload.file_hash,
                project_id=document_upload.project_id,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                uploaded_by=document_upload.user_id
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            processing_task.document_id = document.id
            db.commit()
            
            temp_file_path = document_upload.temp_path
            
            if not os.path.exists(temp_file_path):
                raise Exception(f"Temporary file not found: {temp_file_path}")
            
            if self.s3_client:
                s3_path = f"project_{document_upload.project_id}/{document_upload.file_hash}/{document_upload.file_name}"
                
                try:
                    with open(temp_file_path, "rb") as f:
                        self.s3_client.upload_fileobj(
                            f, 
                            self.bucket_name,
                            s3_path,
                            ExtraArgs={"ContentType": document_upload.content_type}
                        )
                    
                    document.file_path = f"s3://{self.bucket_name}/{s3_path}"
                    db.commit()
                    
                except Exception as e:
                    raise Exception(f"Error uploading to S3: {str(e)}")
                
            else:
                perm_path = f"project_{document_upload.project_id}/documents/{document_upload.file_hash}_{document_upload.file_name}"
                os.makedirs(os.path.dirname(perm_path), exist_ok=True)
                
                try:
                    shutil.copy2(temp_file_path, perm_path)
                    document.file_path = perm_path
                    db.commit()
                except Exception as e:
                    raise Exception(f"Error copying to permanent location: {str(e)}")
            
            processing_task.status = "completed"
            document_upload.status = "completed"
            processing_task.updated_at = datetime.now(UTC)
            db.commit()
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
        except Exception as e:
            try:
                processing_task = db.query(ProcessingTask).filter(
                    ProcessingTask.id == processing_task_id
                ).first()
                
                if processing_task:
                    processing_task.status = "error"
                    processing_task.error_message = str(e)
                    processing_task.updated_at = datetime.now(UTC)
                
                document_upload = db.query(DocumentUpload).filter(
                    DocumentUpload.id == processing_task.document_upload_id
                ).first()
                
                if document_upload:
                    document_upload.status = "error"
                    document_upload.error_message = str(e)
                
                db.commit()
                
            except Exception as inner_e:
                print(f"Error updating task status: {str(inner_e)}")
                
            print(f"Error processing document: {str(e)}")
            
        finally:
            db.close()
    
    async def get_processing_status(self, upload_ids: List[int]) -> Dict:
        """
        Get the processing status for a list of document uploads
        
        Args:
            upload_ids: List of document upload IDs to check
            
        Returns:
            Dict: Status information for each upload
        """
        result = {}
        
        # Fetch all document uploads at once
        document_uploads = self.db.query(DocumentUpload).filter(
            DocumentUpload.id.in_(upload_ids)
        ).all()
        
        # Create a lookup dictionary for uploads
        upload_dict = {upload.id: upload for upload in document_uploads}
        
        # Fetch all processing tasks at once
        processing_tasks = self.db.query(ProcessingTask).filter(
            ProcessingTask.document_upload_id.in_(upload_ids)
        ).all()
        
        # Create a lookup dictionary for tasks by document_upload_id
        task_dict = {task.document_upload_id: task for task in processing_tasks}
        
        for upload_id in upload_ids:
            document_upload = upload_dict.get(upload_id)
            
            if not document_upload:
                result[upload_id] = {"status": "not_found"}
                continue
            
            processing_task = task_dict.get(upload_id)
            
            status_info = {
                "status": document_upload.status,
                "file_name": document_upload.file_name
            }
            
            if document_upload.status == "error":
                status_info["error"] = document_upload.error_message
                
            if processing_task:
                status_info["task_id"] = processing_task.id
                status_info["task_status"] = processing_task.status
                
                if processing_task.document_id:
                    status_info["document_id"] = processing_task.document_id
            
            result[upload_id] = status_info
            
        return result
    
    def validate_file(file: UploadFile):
    # Check file extension
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"File size exceeds the {MAX_FILE_SIZE_MB}MB limit.")

        # Check file name length
        if len(file.filename) > MAX_FILE_NAME_LENGTH:
            # Change the file name to a shorter name
            new_file_name = file.filename[:MAX_FILE_NAME_LENGTH]
            file.filename = new_file_name

    async def document_to_markdown(self, file: UploadFile) -> str:
        try:
            # Validate the file
            self.validate_file(file)

            # Save the file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                temp_file.write(file.file.read())
                temp_file_path = temp_file.name

            md = MarkItDown(enable_plugins=False) 
            result = md.convert(temp_file_path)
            os.remove(temp_file_path)
            if not result:
                raise Exception("Conversion failed.")
            return result.markdown
        except Exception as e:
            raise e
# Factory functions for dependency injection
def get_document_service(db: Session = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db)

def get_document_processing_service(db: Session = Depends(get_db_session)) -> DocumentProcessingService:
    return DocumentProcessingService(db)


