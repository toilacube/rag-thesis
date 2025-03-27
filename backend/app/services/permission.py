from functools import wraps

from fastapi import Depends
from httpx import get
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

def getPermissionService(db: Session = Depends(get_db_session)):
    return PermissionService(db)
