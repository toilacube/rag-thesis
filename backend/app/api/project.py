from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dtos.projectDTO import CreateProjectRequest, ProjectResponse, UpdateProjectRequest
from app.models.models import Project
from db.database import get_db_session

router = APIRouter()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest, db: Session = Depends(get_db_session)
):
    """
    Create a new project.
    """
    new_project = Project(
        project_name=request.project_name,
        description=request.description,
    )
    db.add(new_project)
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

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
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

