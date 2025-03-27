"""insert data

Revision ID: 6ecfa2423206
Revises: 91f5e2aac502
Create Date: 2025-03-27 15:34:56.829423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '6ecfa2423206'
down_revision: Union[str, None] = '91f5e2aac502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create a connection to execute SQL
    conn = op.get_bind()
    
    # Check if user with ID 1 exists
    result = conn.execute(sa.text("SELECT id FROM users WHERE id = 1")).fetchone()
    if not result:
        # Create a new user with ID 1
        # The password hash below is for 'admin123' - you should change this in production
        conn.execute(
            sa.text("""
            INSERT INTO users (id, email, username, hashed_password, is_active, is_superuser, created_at, updated_at)
            VALUES (1, 'admin@example.com', 'admin', '$2b$12$UoT.8YU5ub/oF0OHGLBa/uJOWr/GAJRoVG2OyxchE0UrTGg./1EHK', 
                   TRUE, TRUE, :created_at, :updated_at)
            """),
            {
                "created_at": now,
                "updated_at": now
            }
        )
        print("Created admin user with ID 1")
    
    # Insert permissions
    permissions = [
        ('view_project', 'Can view project details and content', False),
        ('edit_project', 'Can edit project settings and metadata', False),
        ('delete_project', 'Can delete the project', False),
        ('add_document', 'Can add documents to the project', False),
        ('edit_document', 'Can edit documents in the project', False),
        ('delete_document', 'Can delete documents from the project', False),
        ('manage_api_keys', 'Can create and manage API keys for the project', False),
        ('admin', 'Has all permissions for the project', True),
    ]
    
    for name, description, is_system_level in permissions:
        conn.execute(
            sa.text("""
            INSERT INTO permissions (name, description, is_system_level, created_at, updated_at) 
            SELECT :name, :description, :is_system_level, NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name = :name)
            """),
            {
                "name": name,
                "description": description,
                "is_system_level": is_system_level
            }
        )

    # Insert projects
    now = datetime.now()
    projects = [
        ('Customer Support RAG', 'Knowledge base for customer support agents', now, now),
        ('Internal Documentation', 'Company policies and procedures', now, now),
        ('Product Documentation', 'User manuals and technical specifications', now, now),
    ]
    
    for name, description, created_at, updated_at in projects:
        conn.execute(
            sa.text("""
            INSERT INTO projects (project_name, description, created_at, updated_at)
            SELECT :name, :description, :created_at, :updated_at
            WHERE NOT EXISTS (SELECT 1 FROM projects WHERE project_name = :name)
            """),
            {
                "name": name,
                "description": description,
                "created_at": created_at,
                "updated_at": updated_at
            }
        )

    # Get project IDs
    project_ids = {}
    for name in ['Customer Support RAG', 'Internal Documentation', 'Product Documentation']:
        result = conn.execute(
            sa.text("SELECT id FROM projects WHERE project_name = :name"),
            {"name": name}
        ).fetchone()
        if result:
            project_ids[name] = result[0]

    # Get permission IDs
    permission_ids = {}
    for name in ['view_project', 'edit_project', 'delete_project', 'add_document', 
                 'edit_document', 'delete_document', 'manage_api_keys', 'admin']:
        result = conn.execute(
            sa.text("SELECT id FROM permissions WHERE name = :name"),
            {"name": name}
        ).fetchone()
        if result:
            permission_ids[name] = result[0]

    # For the first project, give full access
    if 'Customer Support RAG' in project_ids:
        for perm in ['view_project', 'edit_project', 'delete_project', 'add_document', 
                     'edit_document', 'delete_document', 'manage_api_keys']:
            if perm in permission_ids:
                conn.execute(
                    sa.text("""
                    INSERT INTO project_permissions 
                    (project_id, user_id, permission_id, created_at, updated_at)
                    SELECT :project_id, 1, :permission_id, NOW(), NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM project_permissions 
                        WHERE project_id = :project_id AND user_id = 1 AND permission_id = :permission_id
                    )
                    """),
                    {
                        "project_id": project_ids['Customer Support RAG'],
                        "permission_id": permission_ids[perm]
                    }
                )

    # For the second project, give view and add document access
    if 'Internal Documentation' in project_ids:
        for perm in ['view_project', 'add_document']:
            if perm in permission_ids:
                conn.execute(
                    sa.text("""
                    INSERT INTO project_permissions 
                    (project_id, user_id, permission_id, created_at, updated_at)
                    SELECT :project_id, 1, :permission_id, NOW(), NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM project_permissions 
                        WHERE project_id = :project_id AND user_id = 1 AND permission_id = :permission_id
                    )
                    """),
                    {
                        "project_id": project_ids['Internal Documentation'],
                        "permission_id": permission_ids[perm]
                    }
                )

    # For the third project, give view-only access
    if 'Product Documentation' in project_ids and 'view_project' in permission_ids:
        conn.execute(
            sa.text("""
            INSERT INTO project_permissions 
            (project_id, user_id, permission_id, created_at, updated_at)
            SELECT :project_id, 1, :permission_id, NOW(), NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM project_permissions 
                WHERE project_id = :project_id AND user_id = 1 AND permission_id = :permission_id
            )
            """),
            {
                "project_id": project_ids['Product Documentation'],
                "permission_id": permission_ids['view_project']
            }
        )

def downgrade():
    # Get a connection
    conn = op.get_bind()
    
    # Get project IDs to clean up
    project_names = ['Customer Support RAG', 'Internal Documentation', 'Product Documentation']
    for name in project_names:
        # Find project ID
        result = conn.execute(
            sa.text("SELECT id FROM projects WHERE project_name = :name"),
            {"name": name}
        ).fetchone()
        
        if result:
            project_id = result[0]
            
            # Delete permissions for user 1 on this project
            conn.execute(
                sa.text("DELETE FROM project_permissions WHERE project_id = :project_id AND user_id = 1"),
                {"project_id": project_id}
            )
            
            # Delete the project
            conn.execute(
                sa.text("DELETE FROM projects WHERE id = :project_id"),
                {"project_id": project_id}
            )
