from typing import List
from fastapi import APIRouter, Depends, HTTPException

from backend.app.dtos.projectDTO import CreateProjectRequest
from backend.app.models.models import Project
from db.database import get_db_session
from sqlalchemy.orm import Session 

router = APIRouter()

@router.get("", response_model=CreateProjectRequest)
async def get_projects(
    db: Session = Depends(get_db_session),
) -> List[Project]:
    """
    Retrieve projects that this user has access to.
    """
    pass

