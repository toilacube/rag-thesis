from functools import wraps
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Permission, ProjectPermission
from db.database import get_db_session


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def getUserScopes(self, user_id: int = None):
        # This function creates a scope for the permission check
        # You can customize this function to create the scope you need

        permissions = self.db.query(
            ProjectPermission.project_id,
            ProjectPermission.user_id,
            Permission.name.label('permission_name'),
            Permission.description,
            Permission.is_system_level
        ).join(
            Permission, 
            ProjectPermission.permission_id == Permission.id
        ).filter(
            ProjectPermission.user_id == user_id
        ).all()

        scopes = []

        for permi in permissions:
            scopes.append(f"{permi.project_id}:{permi.permission_name}")

        return scopes
    
    def check_permission(self, user_id: int, project_id: int, required_permission: str) -> bool:
        """
        Check if a user has a specific permission for a project
        
        Args:
            user_id: The ID of the user
            project_id: The ID of the project
            required_permission: The permission name to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Get user scopes
        scopes = self.getUserScopes(user_id)
        
        # Check if the required scope exists
        required_scope = f"{project_id}:{required_permission}"
        
        # Also check for admin permission which grants all permissions
        admin_scope = f"{project_id}:admin"
        
        return required_scope in scopes or admin_scope in scopes


def getPermissionService(db: Session = Depends(get_db_session)):
    return PermissionService(db)


def require_permission(permission_name: str, project_id_param: str = "project_id"):
    """
    Decorator to check if a user has the required permission for a project
    
    Args:
        permission_name: The permission name required (e.g., 'add_document')
        project_id_param: The parameter name that contains the project ID in the endpoint
            
    Example usage:
        @router.post("/upload")
        @require_permission("add_document")
        async def upload_document(project_id: int, user_id: int):
            # This function will only execute if the user has 'add_document' permission
            return {"message": "Document uploaded successfully"}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the database session
            db = next(get_db_session())
            
            # Get the permission service
            permission_service = PermissionService(db)
            
            # Extract the project_id and user_id from kwargs
            project_id = kwargs.get(project_id_param)
            user_id = kwargs.get("user_id")
            
            # If project_id is not in kwargs, try to get it from Form data
            if not project_id and "form_data" in kwargs:
                project_id = kwargs["form_data"].get(project_id_param)
            
            # Check if we have both project_id and user_id
            if not project_id or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing project_id or user_id"
                )
            
            # Check permission
            has_permission = permission_service.check_permission(
                user_id=user_id,
                project_id=project_id,
                required_permission=permission_name
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User does not have '{permission_name}' permission for this project"
                )
            
            # If permission check passes, call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
