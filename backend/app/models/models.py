from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import UTC, datetime

Base = declarative_base()

# Users Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    chats = relationship("Chat", back_populates="user")
    documents = relationship("Document", back_populates="uploaded_by_user")
    document_uploads = relationship("DocumentUpload", back_populates="user")
    project_permissions = relationship("ProjectPermission", back_populates="user")

# Projects Table
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    api_keys = relationship("ApiKey", back_populates="project")
    chat_projects = relationship("ChatProject", back_populates="project")
    document_uploads = relationship("DocumentUpload", back_populates="project")
    documents = relationship("Document", back_populates="project")
    document_chunks = relationship("DocumentChunk", back_populates="project")
    project_permissions = relationship("ProjectPermission", back_populates="project")

# API Keys Table
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key = Column(String(128), nullable=False)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    project = relationship("Project", back_populates="api_keys")

# Chats Table
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")
    chat_projects = relationship("ChatProject", back_populates="chat")

# Messages Table
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    chat = relationship("Chat", back_populates="messages")

# Chat-Project Association Table
class ChatProject(Base):
    __tablename__ = "chat_project"

    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)

    chat = relationship("Chat", back_populates="chat_projects")
    project = relationship("Project", back_populates="chat_projects")

# Document Uploads Table
class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    temp_path = Column(String(255), nullable=False) # Path to the initially uploaded file
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)) # For consumer updates
    status = Column(String(50), default="pending") # e.g., pending, queued, processing, completed, error
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True) # Link to the processed Document

    project = relationship("Project", back_populates="document_uploads")
    user = relationship("User", back_populates="document_uploads")
    document = relationship("Document", back_populates="document_upload_entry") # New relationship

# Documents Table
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(255), nullable=False) # Permanent storage path (S3 or local)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    content_type = Column(String(100))
    file_hash = Column(String(64))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC)) # When document record (post-processing) is created
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False) # User who initiated the upload

    project = relationship("Project", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="documents")
    document_chunks = relationship("DocumentChunk", back_populates="document")
    document_upload_entry = relationship("DocumentUpload", back_populates="document", uselist=False) # Link back to DocumentUpload

# Document Chunks Table
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_name = Column(String(255), nullable=False) # Original file name for context
    hash = Column(String(64), nullable=False) # Hash of the original file
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_metadata = Column(JSON) # Includes text, original chunk metadata, etc.

    project = relationship("Project", back_populates="document_chunks")
    document = relationship("Document", back_populates="document_chunks")

# Permissions Table
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_system_level = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

# Project Permissions Table
class ProjectPermission(Base):
    __tablename__ = "project_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    project = relationship("Project", back_populates="project_permissions")
    user = relationship("User", back_populates="project_permissions")