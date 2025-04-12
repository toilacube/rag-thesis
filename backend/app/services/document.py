'''
TODO list:
- upload document:
    - check if document already exists
    - check if document is valid
    - check if document is in correct format
    - check if document is in correct size
    - check if document is in correct type
    - upload document to S3 (mini IO)
    - save document metadata to database
- process document
'''

import os
import hashlib
import shutil
import boto3
from fastapi import Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import UTC, datetime

from app.models.models import Document, DocumentUpload, ProcessingTask, Project
from app.config.config import getConfig
from db.database import get_db_session

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
            
            # Create bucket if it doesn't exist
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
            except:
                s3_client.create_bucket(Bucket=self.bucket_name)
                
            return s3_client
        except Exception as e:
            # Log the error but continue - we'll handle S3 errors during upload
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
        return processing_task
    
    async def upload_document(
        self, 
        file: UploadFile, 
        project_id: int, 
        user_id: int
    ) -> DocumentUpload:
        """
        Upload a document, validating it and creating necessary database records.
        
        Args:
            file: The file to upload
            project_id: ID of the project to associate the document with
            user_id: ID of the user uploading the document
            
        Returns:
            DocumentUpload: The created document upload record
            
        Raises:
            HTTPException: If validation fails or other errors occur
        """
        # STEP 1: Validate project existence
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # STEP 2: Validate file type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )
        
        # STEP 3: Read file content for validation and hash calculation
        try:
            # Move the file pointer to the beginning
            await file.seek(0)
            content = await file.read()
            file_size = len(content)
            
            # Reset file pointer for later use
            await file.seek(0)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading file: {str(e)}"
            )
        
        # STEP 4: Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)"
            )
        
        # STEP 5: Calculate file hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        # STEP 6: Check if the exact same document already exists in this project
        existing_document = self.db.query(Document).filter(
            Document.project_id == project_id,
            Document.file_hash == file_hash
        ).first()
        
        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document already exists in this project: {existing_document.file_name}"
            )
        
        # STEP 7: Save file to temporary location
        upload_folder = self.config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        
        temp_file_path = os.path.join(upload_folder, f"{file_hash}_{file.filename}")
        
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
        finally:
            # Reset file pointer
            await file.seek(0)
        
        # STEP 8: Create document upload record
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
        except IntegrityError as e:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating document upload record: {str(e)}"
            )
        
        # STEP 9: Upload file to S3/MinIO
        try:
            # Update status to processing
            document_upload.status = "processing"
            self.db.commit()
            
            # Upload to S3/MinIO if client is available
            if self.s3_client:
                s3_path = f"project_{project_id}/{file_hash}/{file.filename}"
                
                with open(temp_file_path, "rb") as f:
                    self.s3_client.upload_fileobj(
                        f, 
                        self.bucket_name,
                        s3_path,
                        ExtraArgs={"ContentType": file.content_type}
                    )
                
                # Create document record with S3 path
                file_path = f"s3://{self.bucket_name}/{s3_path}"
            else:
                # Use local path if S3 client is not available
                file_path = temp_file_path
            
            # Create document record
            document = self._create_document(
                file_path=file_path,
                file_name=file.filename,
                file_size=file_size,
                content_type=file.content_type,
                file_hash=file_hash,
                project_id=project_id,
                user_id=user_id
            )
            
            # Create processing task
            self._create_processing_task(
                project_id=project_id,
                document_id=document.id,
                document_upload_id=document_upload.id,
                user_id=user_id
            )
            
            # Update document upload status to completed
            document_upload.status = "completed"
            self.db.commit()
            self.db.refresh(document_upload)
                
        except Exception as e:
            # Update document upload status to error
            document_upload.status = "error"
            document_upload.error_message = str(e)
            self.db.commit()
            
            # Clean up temporary file 
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file to storage: {str(e)}"
            )
        
        return document_upload
    
    
# Factory function for dependency injection
def get_document_service(db: Session = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db)


