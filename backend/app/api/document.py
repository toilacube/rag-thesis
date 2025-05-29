from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict
import hashlib # For hashing string content
import os # For temp file operations
import shutil # For temp file operations
from datetime import UTC, datetime # For timestamps

from app.dtos.documentDTO import (
    DocumentResponse, 
    DocumentUploadResult, 
    ProcessingStatusResponse,
    DocumentWithStatusResponse,
    DocumentUploadStringRequest # --- IMPORT NEW DTO ---
)
from app.dtos.qdrantDTO import SearchQueryRequest, SearchResponse, SearchResultItem
from app.services.document import (
    DocumentService, 
    DocumentProcessingService, 
    get_document_service, 
    get_document_processing_service,
    ALLOWED_CONTENT_TYPES, # Import for validation
    MAX_FILE_SIZE,         # Import for validation
    create_temp_file_path  # Utility for temp files
)
from app.services.qdrant_service import QdrantService, get_qdrant_service
from app.services.permission import require_permission
from app.services.rabbitmq import RabbitMQService, get_rabbitmq_service # For direct use in test endpoint
from db.database import get_db_session
from app.core.security import get_current_user
from app.models.models import Project, User, Document, DocumentUpload # Import DocumentUpload
from app.config.config import getConfig # For RabbitMQ queue name

router = APIRouter()
import logging
logger = logging.getLogger(__name__)  # Create a proper logger instance

@router.post(
    "/upload", 
    response_model=List[DocumentUploadResult],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload multiple documents to a project for asynchronous processing",
    description="Uploads document files. Files are queued for processing via RabbitMQ."
)
async def upload_documents(
    files: List[UploadFile] = File(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    return await document_service.upload_documents(
        files=files,
        project_id=project_id,
        user_id=current_user.id
    )

# --- NEW TEST ENDPOINT ---
@router.post(
    "/test-upload-string",
    response_model=DocumentUploadResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Test document processing by uploading content as a string",
    description="Accepts document content as a string, saves it to a temporary file, and queues it for processing via RabbitMQ. Intended for testing."
)
# @require_permission("add_document", project_id_param="request_data.project_id") # Protect like normal upload
async def test_upload_document_string(
    request_data: DocumentUploadStringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session), # Direct DB access
    rabbitmq_service: RabbitMQService = Depends(get_rabbitmq_service), # Direct RabbitMQ access
    app_config: dict = Depends(getConfig) # To get queue name
):
    project_id = request_data.project_id
    file_name = request_data.file_name
    document_content = request_data.document_content
    content_type = request_data.content_type

    file_result = {"file_name": file_name, "status": "error", "upload_id": None, "document_id": None, "is_exist": False, "error": None}

    try:
        # Basic validation (similar to DocumentService)
        if content_type not in ALLOWED_CONTENT_TYPES:
            # If MarkItDown can handle text/plain for various inputs, this might be relaxed.
            # For now, keeping it consistent.
            file_result["error"] = f"Unsupported content type: {content_type}"
            logger.warning(f"Unsupported content type for string upload {file_name}: {content_type}")
            # Not raising HTTPException here, return in DocumentUploadResult
            return DocumentUploadResult(**file_result)


        content_bytes = document_content.encode('utf-8')
        file_size = len(content_bytes)

        if file_size == 0:
            file_result["error"] = "Document content is empty."
            return DocumentUploadResult(**file_result)

        if file_size > MAX_FILE_SIZE:
            file_result["error"] = f"Document content size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)"
            return DocumentUploadResult(**file_result)

        file_hash = hashlib.sha256(content_bytes).hexdigest()

        existing_document = db.query(Document).filter(
            Document.project_id == project_id,
            Document.file_hash == file_hash
        ).first()

        if existing_document:
            file_result["status"] = "exists"
            file_result["document_id"] = existing_document.id
            file_result["is_exist"] = True
            logger.info(f"Document from string {file_name} (hash: {file_hash}) already exists in project {project_id}.")
            return DocumentUploadResult(**file_result)

        # Create a temporary file from the string content
        temp_file_path = create_temp_file_path(file_name)
        try:
            with open(temp_file_path, "wb") as buffer: # Write as bytes
                buffer.write(content_bytes)
        except Exception as e:
            file_result["error"] = f"Error saving string content to temporary file: {e}"
            logger.error(f"Error saving string content for {file_name} to temp file: {e}", exc_info=True)
            if os.path.exists(temp_file_path): os.remove(temp_file_path) # Clean up partial file
            return DocumentUploadResult(**file_result)
        
        now = datetime.now(UTC)
        document_upload = DocumentUpload(
            project_id=project_id,
            file_name=file_name,
            file_hash=file_hash,
            file_size=file_size,
            content_type=content_type, # Use provided or defaulted content_type
            temp_path=temp_file_path,
            user_id=current_user.id,
            status="queued",
            created_at=now,
            updated_at=now
        )
        
        db.add(document_upload)
        db.commit()
        db.refresh(document_upload)

        message_body = {"document_upload_id": document_upload.id}
        published = rabbitmq_service.publish_message(
            queue_name=app_config.RABBITMQ_DOCUMENT_QUEUE, # Use config for queue name
            message=message_body
        )

        if published:
            file_result["status"] = "queued"
            file_result["upload_id"] = document_upload.id
            logger.info(f"String content {file_name} (upload_id: {document_upload.id}) queued for processing via RabbitMQ.")
        else:
            document_upload.status = "error"
            document_upload.error_message = "Failed to queue string content for processing."
            db.commit() # Save error status
            file_result["status"] = "error"
            file_result["upload_id"] = document_upload.id
            file_result["error"] = "Failed to queue for processing."
            logger.error(f"Failed to publish message to RabbitMQ for string DocumentUpload {document_upload.id}.")
        
        return DocumentUploadResult(**file_result)

    except HTTPException: # Re-raise HTTPExceptions from permission decorator or explicit checks
        raise
    except Exception as e:
        logger.error(f"Unexpected error during string upload of file '{file_name}': {e}", exc_info=True)
        db.rollback() # Rollback DB changes
        file_result["error"] = f"Unexpected server error: {e}"
        # Clean up temp file if created and error occurred before MQ publishing logic
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path) and file_result["status"] == "error":
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_e:
                logger.error(f"Error cleaning up temp file {temp_file_path} after string upload error: {cleanup_e}")
        
        # For unhandled exceptions, it's better to raise an HTTPException
        # to ensure FastAPI's error handling kicks in, rather than returning a 202 with an error payload.
        # However, the current structure returns DocumentUploadResult.
        # If we want to adhere to that:
        # return DocumentUploadResult(**file_result)
        # If we want to return 500 for unexpected errors:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- END NEW TEST ENDPOINT ---


@router.get(
    "/upload/status",
    response_model=Dict[int, ProcessingStatusResponse], 
    summary="Get document processing status by upload IDs",
    description="Retrieves the current processing status for a list of document uploads."
)
async def get_upload_statuses(
    upload_ids: List[int] = Query(..., description="List of DocumentUpload IDs to check status for."), 
    current_user: User = Depends(get_current_user), 
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    statuses = await processing_service.get_processing_status(upload_ids)
    return statuses


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get processed document by ID",
    description="Retrieve information for a successfully processed document."
)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # @require_permission("view_project" with project_id from document)
    # This requires fetching the document first, then checking permission.
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Manually trigger a permission check for the document's project
    # This is a simplified way; your decorator might need adaptation or a helper function
    # to check permissions on a resource fetched *within* the endpoint.
    temp_permission_check_decorator = require_permission("view_project", project_id_param="project_id_for_check")
    
    async def placeholder_func(project_id_for_check: int, user: User, session: Session):
        return document # The actual return value of this placeholder doesn't matter here

    # This is a bit of a workaround to use the decorator pattern.
    # You might have a direct permission service call here instead.
    # await temp_permission_check_decorator(placeholder_func)(project_id_for_check=document.project_id, current_user=current_user, db=db)
    # The above is complex. A simpler approach for inline check:
    # permission_service = getPermissionService(db) # You'd need to import this
    # if not current_user.is_superuser and \
    #    not permission_service.check_permission(current_user.id, document.project_id, "view_project"):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this document")


    return document


@router.get(
    "/project/{project_id}",
    response_model=List[DocumentResponse],
    summary="Get all processed documents by project ID",
    description="Retrieve all successfully processed documents belonging to a specific project."
)
@require_permission("view_project", project_id_param="project_id")
async def get_documents_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return documents


@router.get(
    "/project/{project_id}/with-status",
    response_model=List[DocumentWithStatusResponse],
    summary="Get documents by project ID with their processing status",
    description="Retrieve all document uploads for a project, showing their current processing status and links to processed documents if available."
)
@require_permission("view_project", project_id_param="project_id")
async def get_documents_with_status_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    docs_with_status_dicts = await document_service.get_documents_with_status(project_id)
    return [DocumentWithStatusResponse.model_validate(d) for d in docs_with_status_dicts]


@router.post(
    "/search_chunks",
    response_model=SearchResponse,
    summary="Search document chunks via Qdrant",
    description="Search for relevant document chunks using vector similarity search."
)
async def search_document_chunks(
    request: SearchQueryRequest,
    current_user: User = Depends(get_current_user),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    db: Session = Depends(get_db_session)
):
    if request.project_id:
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {request.project_id} not found.")
        # TODO: Add permission check: require_permission("view_project", project_id=request.project_id)

    try:
        search_hits = qdrant_service.search_chunks(
            query_text=request.query_text,
            project_id=request.project_id,
            limit=request.limit
        )
        
        results = []
        for hit in search_hits:
            payload = hit.payload if hit.payload else {}
            results.append(SearchResultItem(
                chunk_id=str(hit.id),
                document_id=payload.get("document_id"),
                project_id=payload.get("project_id"),
                file_name=payload.get("file_name", "N/A"),
                score=hit.score,
                text=payload.get("text", ""),
                metadata=payload.get("chunk_metadata", {})
            ))
        return SearchResponse(results=results)
        
    except RuntimeError as e: # Catch specific errors from QdrantService
        logger.error(f"Runtime error during Qdrant search: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Search service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Qdrant search: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during search.")

import os
import json
import boto3
from fastapi.responses import PlainTextResponse
from urllib.parse import urlparse

@router.get(
    "/{document_id}/markdown",
    response_class=PlainTextResponse,
    summary="Get markdown content for a document",
    description="Retrieves the extracted/converted markdown content for a document. Returns plain text markdown."
)
async def get_document_markdown(
    document_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    app_config: dict = Depends(getConfig)
):
    # First get the document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check for permission to view the document (like in get_document endpoint)
    temp_permission_check_decorator = require_permission("view_project", project_id_param="project_id_for_check")
    
    async def placeholder_func(project_id_for_check: int, user: User, session: Session):
        return document
        
    await temp_permission_check_decorator(placeholder_func)(project_id_for_check=document.project_id, current_user=current_user, db=db)
    
    # Check if markdown_s3_link exists
    if not document.markdown_s3_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Markdown content not available for this document"
        )
    
    # Get markdown content from S3 or local file depending on the link format
    markdown_content = ""
    if document.markdown_s3_link.startswith("s3://"):
        # Parse S3 URL
        parsed_url = urlparse(document.markdown_s3_link)
        bucket_name = parsed_url.netloc
        s3_key = parsed_url.path.lstrip("/")
        
        # Create S3 client
        endpoint_url = app_config.MINIO_ENDPOINT
        access_key = app_config.MINIO_ACCESS_KEY
        secret_key = app_config.MINIO_SECRET_KEY
        
        if not all([endpoint_url, access_key, secret_key, bucket_name]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 storage not properly configured"
            )
            
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1', 
            config=boto3.session.Config(signature_version='s3v4')
        )
        
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            markdown_content = response['Body'].read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error retrieving markdown content from S3: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve markdown content: {str(e)}"
            )
    else:
        # Assuming it's a local file path
        if not os.path.exists(document.markdown_s3_link):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Markdown file not found at the specified location"
            )
        
        try:
            with open(document.markdown_s3_link, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except Exception as e:
            logger.error(f"Error reading local markdown file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read markdown content: {str(e)}"
            )
    
    return markdown_content