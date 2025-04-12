from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentUploadBase(BaseModel):
    project_id: int
    file_name: str
    file_size: int
    content_type: str


class DocumentUploadResponse(DocumentUploadBase):
    id: int
    file_hash: str
    status: str
    created_at: datetime
    error_message: Optional[str] = None

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
    created_at: datetime
    updated_at: datetime
    uploaded_by: int

    class Config:
        from_attributes = True


class ProcessingTaskResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    document_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    document_upload_id: Optional[int] = None
    
    class Config:
        from_attributes = True