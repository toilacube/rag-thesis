from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.dtos.messageDTO import MessageResponse # Import MessageResponse

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    project_id: int # Link chat to a single project for RAG context

class ChatResponse(ChatBase):
    id: int
    user_id: int
    project_id: int # Store the linked project ID
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True