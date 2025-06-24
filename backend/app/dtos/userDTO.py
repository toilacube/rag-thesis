from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# DTOs for User Permission Management
class UserPermissionDTO(BaseModel):
    user_id: int
    project_id: int
    permission_id: int

class AddUserToProjectRequest(BaseModel):
    email: EmailStr
    permissions: List[str]

class UserProjectPermissionResponse(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    project_id: int
    permissions: List[str]

class BatchUserAssignment(BaseModel):
    users: List[AddUserToProjectRequest]