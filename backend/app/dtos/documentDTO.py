from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentUploadBase(BaseModel):
    project_id: int
    file_name: str
    file_size: int
    content_type: str


class DocumentUploadResponse(DocumentUploadBase):
    id: int
    file_hash: str
    status: str # e.g. pending, queued, processing, completed, error
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    document_id: Optional[int] = None # ID of the processed Document record

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_hash: Optional[str] = None
    project_id: int
    markdown_s3_link: Optional[str] = None  # Link to the extracted markdown text
    created_at: datetime
    updated_at: datetime
    uploaded_by: int

    class Config:
        from_attributes = True


class DocumentUploadResult(BaseModel): # Used as return for upload endpoint for each file
    file_name: str
    status: str # e.g. "queued", "exists", "error"
    upload_id: Optional[int] = None
    document_id: Optional[int] = None # If status is "exists"
    is_exist: bool # True if document (by hash) already exists in project
    error: Optional[str] = None


class ProcessingStatusResponse(BaseModel): # Used for GET /upload/status
    upload_id: int
    file_name: str
    upload_status: str # Status from DocumentUpload
    upload_error: Optional[str] = None
    document_id: Optional[int] = None # If processing led to a Document record


class DocumentWithStatusResponse(BaseModel):
    id: int # Document ID
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_hash: Optional[str] = None
    project_id: int
    markdown_s3_link: Optional[str] = None  # Link to the extracted markdown text
    created_at: datetime # Document creation time
    updated_at: datetime # Document update time
    uploaded_by: int
    processing_status: Optional[str] = None # Derived status: e.g., completed, processing, error, pending_upload
    error_message: Optional[str] = None # Error from DocumentUpload if processing failed
    upload_id: Optional[int] = None # ID of the corresponding DocumentUpload entry

    class Config:
        from_attributes = True

# --- NEW DTO for string upload test ---
class DocumentUploadStringRequest(BaseModel):
    project_id: int
    file_name: str = Field(..., example="test_document.md")
    document_content: str
    content_type: str = Field(default="text/markdown", example="text/markdown") # Allow override, default to markdown