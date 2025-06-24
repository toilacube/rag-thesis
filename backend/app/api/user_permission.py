from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import EmailStr

from app.core.api_reponse import api_response
from app.models.models import User, ProjectPermission, Permission, Project
from app.dtos.userDTO import UserPermissionDTO, UserProjectPermissionResponse, AddUserToProjectRequest, BatchUserAssignment
from db.database import get_db_session
from app.core.security import get_current_user
from app.services.permission import (
    PermissionService, 
    getPermissionService, 
    require_permission, 
    require_manage_users_or_superuser
)

router = APIRouter()

@router.post("/project/{project_id}/user-assignment", response_model=UserProjectPermissionResponse)
@require_manage_users_or_superuser()
async def add_user_to_project(
    project_id: int,
    request: AddUserToProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Add a user to a project with specific permissions.
    
    Args:
        project_id: ID of the project
        request: User email and permissions to add
        
    Returns:
        Information about the user and granted permissions
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Find the user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {request.email} not found"
        )
    
    # Get all permission IDs for the requested permission names
    permissions = db.query(Permission).filter(
        Permission.name.in_(request.permissions)
    ).all()
    
    if len(permissions) != len(request.permissions):
        # Some requested permissions don't exist
        found_permission_names = [p.name for p in permissions]
        missing_permissions = [p for p in request.permissions if p not in found_permission_names]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions: {', '.join(missing_permissions)}"
        )
    
    # Add permissions for the user to the project
    for permission in permissions:
        # Check if the permission already exists
        existing_permission = db.query(ProjectPermission).filter(
            ProjectPermission.project_id == project_id,
            ProjectPermission.user_id == user.id,
            ProjectPermission.permission_id == permission.id
        ).first()
        
        if not existing_permission:
            # Create new permission
            project_permission = ProjectPermission(
                project_id=project_id,
                user_id=user.id,
                permission_id=permission.id
            )
            db.add(project_permission)
    
    db.commit()
    
    # Return the user's permissions for the project
    project_permissions = db.query(
        Permission.name
    ).join(
        ProjectPermission, 
        ProjectPermission.permission_id == Permission.id
    ).filter(
        ProjectPermission.project_id == project_id,
        ProjectPermission.user_id == user.id
    ).all()
    
    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "project_id": project_id,
        "permissions": [p[0] for p in project_permissions]
    }

@router.post("/project/{project_id}/users-batch-assignment")
@require_manage_users_or_superuser()
async def assign_users_to_project_batch(
    project_id: int,
    request: BatchUserAssignment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    responses = []

    for item in request.users:
        user = db.query(User).filter(User.email == item.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {item.email} not found"
            )

        permissions = db.query(Permission).filter(
            Permission.name.in_(item.permissions)
        ).all()

        if len(permissions) != len(item.permissions):
            found_permission_names = [p.name for p in permissions]
            missing_permissions = [p for p in item.permissions if p not in found_permission_names]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permissions for {item.email}: {', '.join(missing_permissions)}"
            )

        for permission in permissions:
            exists = db.query(ProjectPermission).filter_by(
                project_id=project_id,
                user_id=user.id,
                permission_id=permission.id
            ).first()

            if not exists:
                db.add(ProjectPermission(
                    project_id=project_id,
                    user_id=user.id,
                    permission_id=permission.id
                ))

        responses.append({
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "permissions": [p.name for p in permissions]
        })

    db.commit()
    return {"project_id": project_id, "assigned": responses}

@router.get("/project/{project_id}/users", response_model=List[UserProjectPermissionResponse])
@require_permission("view_project")
async def get_project_users(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get all users and their permissions for a project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        List of users and their permissions for the project
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    users_with_permissions = db.query(
        User.id,
        User.email,
        User.username,
        ProjectPermission.project_id
    ).join(
        ProjectPermission,
        ProjectPermission.user_id == User.id
    ).filter(
        ProjectPermission.project_id == project_id,
        User.id != current_user.id
    ).distinct().all()
    
    result = []
    for user_id, email, username, project_id in users_with_permissions:
        # Get permissions for this user in this project
        permissions = db.query(
            Permission.name
        ).join(
            ProjectPermission,
            ProjectPermission.permission_id == Permission.id
        ).filter(
            ProjectPermission.user_id == user_id,
            ProjectPermission.project_id == project_id
        ).all()
        
        result.append({
            "user_id": user_id,
            "email": email,
            "username": username,
            "project_id": project_id,
            "permissions": [p[0] for p in permissions]
        })
    
    return result

@router.put("/project/{project_id}/user/{user_id}/permissions")
@require_manage_users_or_superuser()
async def update_user_permissions(
    project_id: int,
    user_id: int,
    permissions: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update a user's permissions for a project.
    
    Args:
        project_id: ID of the project
        user_id: ID of the user
        permissions: List of permission names to assign
        
    Returns:
        Updated user permissions
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get permission IDs for the requested permissions
    permission_records = db.query(Permission).filter(
        Permission.name.in_(permissions)
    ).all()
    
    if len(permission_records) != len(permissions):
        # Some requested permissions don't exist
        found_permission_names = [p.name for p in permission_records]
        missing_permissions = [p for p in permissions if p not in found_permission_names]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions: {', '.join(missing_permissions)}"
        )
    
    # Remove all existing permissions for the user in this project
    db.query(ProjectPermission).filter(
        ProjectPermission.project_id == project_id,
        ProjectPermission.user_id == user_id
    ).delete()
    
    # Add the new permissions
    for permission in permission_records:
        project_permission = ProjectPermission(
            project_id=project_id,
            user_id=user_id,
            permission_id=permission.id
        )
        db.add(project_permission)
    
    db.commit()
    
    # Return the updated permissions
    updated_permissions = db.query(
        Permission.name
    ).join(
        ProjectPermission,
        ProjectPermission.permission_id == Permission.id
    ).filter(
        ProjectPermission.project_id == project_id,
        ProjectPermission.user_id == user_id
    ).all()
    
    return api_response(
        data={
            "user_id": user_id,
            "project_id": project_id,
            "permissions": [p[0] for p in updated_permissions]
        },
        message="User permissions updated successfully"
    )

@router.delete("/project/{project_id}/user/{user_id}")
@require_manage_users_or_superuser()
async def remove_user_from_project(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Remove a user from a project by deleting all their permissions.
    
    Args:
        project_id: ID of the project
        user_id: ID of the user to remove
        
    Returns:
        Success message
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent users from removing themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the project"
        )
    
    # Remove all permissions for the user in this project
    result = db.query(ProjectPermission).filter(
        ProjectPermission.project_id == project_id,
        ProjectPermission.user_id == user_id
    ).delete()
    
    db.commit()
    
    if result == 0:
        return api_response(
            data=None,
            message=f"User was not a member of project {project_id}"
        )
    
    return api_response(
        data=None,
        message=f"User {user.email} removed from project {project_id}"
    )