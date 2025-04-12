"""init db

Revision ID: 91f5e2aac502
Revises: 
Create Date: 2025-03-24 11:49:13.521725

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '91f5e2aac502'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema."""
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False),
    )

    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('api_key', sa.String(128), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    # Chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False),
    )

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('chat_id', sa.Integer, sa.ForeignKey('chats.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False),
    )

    # Chat-Project association table
    op.create_table(
        'chat_project',
        sa.Column('chat_id', sa.Integer, sa.ForeignKey('chats.id'), primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), primary_key=True),
    )

    # Document Uploads table
    op.create_table(
        'document_uploads',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('temp_path', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
    )

    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('file_path', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer),
        sa.Column('content_type', sa.String(100)),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False),
        sa.Column('uploaded_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.UniqueConstraint('project_id', 'file_name', name='uq_kb_file_name'),
    )

    # Processing Tasks table
    op.create_table(
        'processing_tasks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id')),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('documents.id')),
        sa.Column('status', sa.String(50)),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP),
        sa.Column('updated_at', sa.TIMESTAMP),
        sa.Column('document_upload_id', sa.Integer, sa.ForeignKey('document_uploads.id')),
        sa.Column('initiated_by', sa.Integer, sa.ForeignKey('users.id')),
    )

    # Document Chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('chunk_metadata', sa.JSON),
    )

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('is_system_level', sa.Boolean, nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    # Project Permissions table
    op.create_table(
        'project_permissions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_by', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.UniqueConstraint('project_id', 'user_id', 'permission_id', name='uq_project_user_permission'),
    )


def downgrade():
    """Downgrade schema."""
    op.drop_table('project_permissions')
    op.drop_table('permissions')
    op.drop_table('document_chunks')
    op.drop_table('processing_tasks')
    op.drop_table('documents')
    op.drop_table('document_uploads')
    op.drop_table('chat_project')
    op.drop_table('messages')
    op.drop_table('chats')
    op.drop_table('api_keys')
    op.drop_table('projects')
    op.drop_table('users')
