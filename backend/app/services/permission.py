from functools import wraps
from typing import List, Optional
import inspect

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Permission, ProjectPermission, User
from db.database import get_db_session
from typing import Union


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


def require_permission(permission_name: Union[str, list[str]], project_id_param: str = "project_id"):
    """
    Decorator to check if a user has one of the required permissions for a project.
    
    Args:
        permission_name: A permission name or list of permission names (e.g., 'add_document' or ['add', 'edit'])
        project_id_param: The parameter name that contains the project ID in the endpoint
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get database and service
            db = next(get_db_session())
            permission_service = PermissionService(db)

            # Extract project_id
            project_id = kwargs.get(project_id_param)
            if project_id is None:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if project_id_param in param_names and len(args) > param_names.index(project_id_param):
                    project_id = args[param_names.index(project_id_param)]

            # Extract current_user
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
                if current_user is None and "current_user" in inspect.signature(func).parameters:
                    param_names = list(sig.parameters.keys())
                    current_user_index = param_names.index("current_user")
                    if len(args) > current_user_index:
                        current_user = args[current_user_index]

            if not project_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing {project_id_param}")
            if not current_user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

            if current_user.is_superuser:
                return await func(*args, **kwargs)

            # Convert to list if single string
            required_permissions = permission_name if isinstance(permission_name, list) else [permission_name]

            if not any(
                permission_service.check_permission(current_user.id, project_id, perm)
                for perm in required_permissions
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User lacks required permissions: {required_permissions}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Simplified version that uses the main decorator
def require_manage_users_or_superuser(project_id_param: str = "project_id"):
    """
    Decorator to check if the current user has 'manage_user' permission or is a superuser
    
    Args:
        project_id_param: The parameter name that contains the project ID in the endpoint
    """
    return require_permission("manage_user", project_id_param)
