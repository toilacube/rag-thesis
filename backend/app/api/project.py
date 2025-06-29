from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.dtos.projectDTO import CreateProjectRequest, ProjectResponse, UpdateProjectRequest
from app.dtos.userDTO import UserResponse
from app.models.models import Project, ProjectPermission
from db.database import get_db_session
from app.core.security import get_current_user
from app.models.models import User

router = APIRouter()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest, db: Session = Depends(get_db_session), current_user: User = Depends(get_current_user)
):
    """
    Create a new project.
    """
    new_project = Project(
        project_name=request.project_name,
        description=request.description,
    )
    db.add(new_project)
    db.flush()
    
    project_permission = ProjectPermission(
        project_id=new_project.id,
        user_id=current_user.id,
        permission_id=8 # admin role?
    )
    db.add(project_permission)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db_session)):
    """
    Retrieve all projects.
    """
    return db.query(Project).all()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db_session)):
    """
    Retrieve a project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, request: UpdateProjectRequest, db: Session = Depends(get_db_session)
):
    """
    Update a project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project.project_name = request.project_name
    project.description = request.description
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(project_id: int, db: Session = Depends(get_db_session)):
    """
    Delete a project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully", "project_id": project_id}

# Get all projects for the current user
@router.get("/user/me")
def get_projects_for_current_user(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_superuser:
        projects_raw = db.query(
            Project.id,
            Project.project_name,
            Project.description,
            db.literal(None).label("user_id"),
            db.literal(None).label("permission_id")
        ).all()
    else:
        projects_raw = db.query(
            Project.id,
            Project.project_name,
            Project.description,
            ProjectPermission.user_id.label("user_id"),
            ProjectPermission.permission_id.label("permission_id")
        ).join(
            ProjectPermission, Project.id == ProjectPermission.project_id
        ).filter(
            ProjectPermission.user_id == current_user.id
        ).all()

    # Group by project_id
    grouped = {}
    for row in projects_raw:
        project_id = row.id
        if project_id not in grouped:
            grouped[project_id] = {
                "id": project_id,
                "project_name": row.project_name,
                "description": row.description,
                "user_id": row.user_id,
                "permission_ids": [],
            }
        if row.permission_id is not None and row.permission_id not in grouped[project_id]["permission_ids"]:
            grouped[project_id]["permission_ids"].append(row.permission_id)

    return list(grouped.values())


@router.get("/{project_id}/unassigned-users", response_model=List[UserResponse])
def get_unassigned_users_for_project(
    project_id: int,
    q: Optional[str] = Query(None, description="Search string in email"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get users who are active and NOT assigned to the given project.
    Can filter by partial email match.
    """
    assigned_user_ids = db.query(ProjectPermission.user_id)\
        .filter(ProjectPermission.project_id == project_id)

    query = db.query(User)\
        .filter(~User.id.in_(assigned_user_ids))\
        .filter(
            User.is_active == True, 
            User.id != current_user.id
        )

    if q:
        query = query.filter(func.lower(User.email).ilike(f"%{q.lower()}%"))

    return query.all()