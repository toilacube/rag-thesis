from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system_level: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
