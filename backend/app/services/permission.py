from functools import wraps
from typing import List, Optional
import inspect

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Permission, ProjectPermission, User
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
    
    def check_is_superuser(self, user_id: int) -> bool:
        """Check if a user is a superuser"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user is not None and user.is_superuser


def getPermissionService(db: Session = Depends(get_db_session)):
    return PermissionService(db)


def require_permission(permission_name: str, project_id_param: str = "project_id"):
    """
    Decorator to check if a user has the required permission for a project
    
    Args:
        permission_name: The permission name required (e.g., 'add_document')
        project_id_param: The parameter name that contains the project ID in the endpoint
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the database session
            db = next(get_db_session())
            
            # Get the permission service
            permission_service = PermissionService(db)
            
            # Extract the project_id from kwargs
            project_id = kwargs.get(project_id_param)
            
            # Extract the current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user and "current_user" in inspect.signature(func).parameters:
                # If the function expects current_user but it's not in kwargs,
                # we're likely in a test environment where it's passed differently
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            # Check if we have project_id
            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {project_id_param} parameter"
                )
            
            # Check if we have current_user
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # If the user is a superuser, they can access any project
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # For non-superusers, check for the required permission
            has_permission = permission_service.check_permission(
                user_id=current_user.id,
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


def require_manage_users_or_superuser(project_id_param: str = "project_id"):
    """
    Decorator to check if the current user has 'manage_user' permission or is a superuser
    
    Args:
        project_id_param: The parameter name that contains the project ID in the endpoint
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the database session
            db = next(get_db_session())
            
            # Get the permission service
            permission_service = PermissionService(db)
            
            # Extract the project_id from kwargs
            project_id = kwargs.get(project_id_param)
            
            # Extract the current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user and "current_user" in inspect.signature(func).parameters:
                # If the function expects current_user but it's not in kwargs,
                # we're likely in a test environment where it's passed differently
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            # Check if we have project_id
            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {project_id_param} parameter"
                )
            
            # Check if we have current_user
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # If the user is a superuser, they can access any project
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # For non-superusers, check for the manage_user permission
            has_permission = permission_service.check_permission(
                user_id=current_user.id,
                project_id=project_id,
                required_permission="manage_user"
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to manage users for this project"
                )
            
            # If permission check passes, call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
