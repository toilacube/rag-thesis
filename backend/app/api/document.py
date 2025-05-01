from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
from functools import wraps

from app.dtos.documentDTO import DocumentUploadResponse, DocumentResponse, ProcessingTaskResponse, DocumentWithStatusResponse
from app.services.document import DocumentService, DocumentProcessingService, get_document_service, get_document_processing_service
from app.services.permission import require_permission
from db.database import get_db_session
from app.core.security import get_current_user
from app.models.models import User

router = APIRouter()

@router.post(
    "/upload", 
    response_model=List[Dict],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple documents to a project",
    description="Upload one or more document files to a specified project. The files will be validated, saved, and queued for processing."
)
async def upload_documents(
    files: List[UploadFile] = File(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Upload multiple documents to a project.
    
    - **files**: The document files to upload (PDF, DOCX, DOC, TXT, MD, XLS, XLSX)
    - **project_id**: ID of the project to upload the documents to
    
    Returns the list of upload results with status information.
    
    Requires 'add_document' permission for the specified project.
    """
    # Use the permission decorator
    # @require_permission("add_document")
    async def _upload_with_permission(files, project_id, user_id, document_service, processing_service):
        try:
            # Upload the documents (validates files and creates DocumentUpload records)
            upload_results = await  document_service.upload_documents(
                files=files,
                project_id=project_id,
                user_id=user_id
            )
            
            # Extract the upload IDs of pending documents that need processing
            # upload_ids = [result["upload_id"] for result in upload_results 
            #              if result["status"] == "pending" and result["upload_id"] is not None]
            
            # # If we have uploads to process, start processing them
            # if upload_ids:
            #     await processing_service.process_documents(
            #         upload_ids=upload_ids,
            #         user_id=user_id
            #     )
            
            return upload_results
            
        except HTTPException as e:
            # Pass through HTTP exceptions from the service
            raise e
        except Exception as e:
            # Log unexpected errors and return a generic message
            print(f"Unexpected error during document upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during document upload"
            )
    
    # Call the wrapped function with permission check
    return await _upload_with_permission(files, project_id, current_user.id, document_service, processing_service)

class UploadIDsRequest(BaseModel):
    upload_ids: List[int]

@router.post(
    "/process",
    # response_model=List[Dict],
    summary="Process documents",
    description="Process documents that have been uploaded but not yet processed"
    )
async def process_documents(
    request: UploadIDsRequest,
    current_user: User = Depends(get_current_user),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Process documents that have been uploaded but not yet processed.
    
    - **upload_ids**: List of document upload IDs to process
    
    Returns the list of processing task results.
    """

    return await processing_service.process_documents(
        upload_ids=request.upload_ids,
        user_id=current_user.id
    )
        

@router.get(
    "/upload/status",
    response_model=Dict,
    summary="Get document processing status",
    description="Get the processing status for a list of document uploads"
)
async def get_processing_status(
    upload_ids: List[int],
    current_user: User = Depends(get_current_user),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Get the processing status for a list of document uploads.
    
    - **upload_ids**: List of document upload IDs to check
    
    Returns status information for each upload.
    """
    return await processing_service.get_processing_status(upload_ids)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
    description="Retrieve document information by its ID"
)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get a document by its ID.
    
    - **document_id**: ID of the document to retrieve
    
    Returns the Document information.
    """
    from app.models.models import Document
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

@router.get(
    "/project/{project_id}",
    response_model=List[DocumentResponse],
    summary="Get documents by project ID",
    description="Retrieve all documents belonging to a project"
)
async def get_documents_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get all documents for a specific project.
    
    - **project_id**: ID of the project to get documents for
    
    Returns a list of Document objects.
    
    Requires 'view_project' permission for the specified project.
    """
    # Use the permission decorator
    @require_permission("view_project", project_id_param="project_id")
    async def _get_documents_with_permission(project_id, current_user, db):
        from app.models.models import Document
        documents = db.query(Document).filter(Document.project_id == project_id).all()
        return documents
    
    # Call the wrapped function with permission check - passing project_id explicitly
    return await _get_documents_with_permission(project_id, current_user, db)

@router.get(
    "/project/{project_id}/with-status",
    response_model=List[DocumentWithStatusResponse],
    summary="Get documents by project ID with processing status",
    description="Retrieve all documents belonging to a project along with their processing status"
)
async def get_documents_with_status_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get all documents with their processing status for a specific project.
    
    - **project_id**: ID of the project to get documents for
    
    Returns a list of documents with their processing status.
    
    Requires 'view_project' permission for the specified project.
    """
    # Use the permission decorator
    @require_permission("view_project")
    async def _get_documents_with_status_permission(project_id, user_id, document_service):
        return await document_service.get_documents_with_status(project_id)
    
    # Call the wrapped function with permission check
    return await _get_documents_with_status_permission(project_id, current_user.id, document_service)
