from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db_session
from app.models.models import Permission
from app.dtos.permissionDTO import PermissionResponse

router = APIRouter()

@router.get("/", response_model=List[PermissionResponse])
def get_permissions(
    db: Session = Depends(get_db_session)
):
    permissions = db.query(Permission).all()
    return permissions
