from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status, Query # Added Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Optional # Added Optional
from functools import wraps

from app.dtos.documentDTO import DocumentUploadResponse, DocumentResponse, ProcessingTaskResponse, DocumentWithStatusResponse
from app.dtos.qdrantDTO import SearchQueryRequest, SearchResponse, SearchResultItem # Added Qdrant DTOs
from app.services.document import DocumentService, DocumentProcessingService, get_document_service, get_document_processing_service
from app.services.qdrant_service import QdrantService, get_qdrant_service # Added QdrantService
from app.services.permission import require_permission # Assuming this exists
from db.database import get_db_session
from app.core.security import get_current_user
from app.models.models import Project, User, Document # Added Document model for direct query

router = APIRouter()

# The commented-out @require_permission and inner function structure in upload_documents
# is kept as per your original code. If require_permission is an async decorator,
# it should ideally wrap the main endpoint function directly.
@router.post(
    "/upload", 
    response_model=List[Dict], # Consider a more specific DTO if structure is fixed
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple documents to a project",
    description="Upload one or more document files to a specified project. The files will be validated, saved, and queued for processing."
)
async def upload_documents(
    files: List[UploadFile] = File(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    # processing_service: DocumentProcessingService = Depends(get_document_processing_service) # Not used directly here
):
    # @require_permission("add_document") # Kept commented as in original
    async def _upload_with_permission(files_param, project_id_param, user_id_param, doc_service_param):
        # This inner function pattern for permissions is unusual.
        # Typically, the decorator handles this on the main function.
        # Assuming 'add_document' permission would be checked here for project_id_param by the decorator.
        return await doc_service_param.upload_documents(
            files=files_param,
            project_id=project_id_param,
            user_id=user_id_param
        )
    
    return await _upload_with_permission(files, project_id, current_user.id, document_service)

class UploadIDsRequest(BaseModel):
    upload_ids: List[int]

@router.post(
    "/process",
    response_model=List[ProcessingTaskResponse], # Assuming ProcessingTaskResponse DTO exists
    summary="Process documents",
    description="Initiate processing for documents that have been uploaded but not yet processed (creates processing tasks)."
)
async def process_documents_endpoint( # Renamed to avoid conflict with service method
    request: UploadIDsRequest,
    current_user: User = Depends(get_current_user),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    # Assuming require_permission for each project related to upload_ids might be complex here.
    # Permission might be checked at a higher level or implicitly by user's access to projects.
    # For now, direct call.
    tasks = await processing_service.process_documents(
        upload_ids=request.upload_ids,
        user_id=current_user.id
    )
    # Map SQLAlchemy Task objects to ProcessingTaskResponse DTOs
    return [ProcessingTaskResponse.model_validate(task) for task in tasks]


@router.get(
    "/upload/status",
    response_model=Dict[int, Dict], # More specific DTO would be better
    summary="Get document processing status",
    description="Get the processing status for a list of document uploads by their upload IDs."
)
async def get_processing_status(
    # FastAPI typically gets list of ints from query like: ?upload_ids=1&upload_ids=2
    upload_ids: List[int] = Query(...), 
    current_user: User = Depends(get_current_user), # Add permission check if needed
    processing_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    # Add permission checks here: e.g., user must have access to projects associated with these upload_ids
    return await processing_service.get_processing_status(upload_ids)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse, # Assuming DocumentResponse DTO exists
    summary="Get document by ID",
    description="Retrieve document information by its ID."
)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user) # Add permission check
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # @require_permission("view_document", document_id_param="document_id") # Or project based
    # Example: check if current_user has permission to view this document's project
    # project_id = document.project_id
    # (await _check_permission_wrapper(project_id, "view_project", current_user, db)) # Your permission logic

    return DocumentResponse.model_validate(document)


@router.get(
    "/project/{project_id}",
    response_model=List[DocumentResponse], # Assuming DocumentResponse DTO exists
    summary="Get documents by project ID",
    description="Retrieve all documents belonging to a project."
)
# @require_permission("view_project", project_id_param="project_id") # Apply decorator directly
async def get_documents_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    # Inline permission or use decorator. For now, direct query after decorator (if active).
    # The decorator should handle the permission check.
    # If using the inner function pattern:
    @require_permission("view_project", project_id_param="project_id_for_perm_check")
    async def _get_documents_with_permission(project_id_for_perm_check: int, user: User, session: Session):
        documents = session.query(Document).filter(Document.project_id == project_id_for_perm_check).all()
        return [DocumentResponse.model_validate(doc) for doc in documents]

    return await _get_documents_with_permission(project_id, current_user, db)


@router.get(
    "/project/{project_id}/with-status",
    response_model=List[DocumentWithStatusResponse], # Assuming this DTO exists
    summary="Get documents by project ID with processing status",
    description="Retrieve all documents for a project with their processing status."
)
# @require_permission("view_project", project_id_param="project_id") # Apply decorator
async def get_documents_with_status_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    @require_permission("view_project", project_id_param="project_id_for_perm_check")
    async def _get_docs_with_status_permission(project_id_for_perm_check: int, user: User, doc_service: DocumentService):
        docs_with_status = await doc_service.get_documents_with_status(project_id_for_perm_check)
        # Ensure docs_with_status items conform to DocumentWithStatusResponse
        return [DocumentWithStatusResponse.model_validate(doc) for doc in docs_with_status]

    return await _get_docs_with_status_permission(project_id, current_user, document_service)

# --- New Qdrant Search Endpoint ---
@router.post(
    "/search_chunks",
    response_model=SearchResponse,
    summary="Search document chunks",
    description="Search for relevant document chunks using vector similarity search in Qdrant."
)
async def search_document_chunks(
    request: SearchQueryRequest,
    current_user: User = Depends(get_current_user), # For permission checks
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    db: Session = Depends(get_db_session) # If needed for additional permission checks
):
    # Permission check: User must have access to the project_id if specified
    if request.project_id:
        # Example permission check (adapt to your system)
        # You would typically use your @require_permission decorator or a similar service method
        # For demonstration, a placeholder check:
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {request.project_id} not found.")
        
        # Your actual permission check, e.g., has_permission(user, "view_project", request.project_id)
        # This is a simplified check; replace with your robust permission logic.
        # Let's assume a simple check for brevity or that it's handled by a decorator if you adapt one.
        # For example:
        # await require_permission_manual_check("view_project", project_id=request.project_id, user=current_user, db=db)

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
                chunk_id=str(hit.id), # Qdrant ID can be int or UUID string
                document_id=payload.get("document_id"),
                project_id=payload.get("project_id"),
                file_name=payload.get("file_name", "N/A"),
                score=hit.score,
                text=payload.get("text", ""),
                metadata=payload.get("chunk_metadata", {})
            ))
        return SearchResponse(results=results)
        
    except RuntimeError as e: # Catch specific errors from QdrantService
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Search service error: {e}")
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during search: {e}")