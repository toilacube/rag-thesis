from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List

from app.dtos.documentDTO import DocumentUploadResponse, DocumentResponse
from app.services.document import DocumentService, get_document_service
from db.database import get_db_session

router = APIRouter()

@router.post(
    "/upload", 
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to a project",
    description="Upload a document file to a specified project. The file will be validated, saved, and queued for processing."
)
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    user_id: int = Form(...),  # In a real app, this would come from token
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document to a project.
    
    - **file**: The document file to upload (PDF, DOCX, DOC, TXT, MD, XLS, XLSX)
    - **project_id**: ID of the project to upload the document to
    - **user_id**: ID of the user uploading the document
    
    Returns the created DocumentUpload record with status information.
    """
    try:
        document_upload = await document_service.upload_document(
            file=file,
            project_id=project_id,
            user_id=user_id
        )
        return document_upload
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
    db: Session = Depends(get_db_session)
):
    """
    Get all documents for a specific project.
    
    - **project_id**: ID of the project to get documents for
    
    Returns a list of Document objects.
    """
    from app.models.models import Document
    
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return documents