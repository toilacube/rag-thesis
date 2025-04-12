-- users table for authentication and user management
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  username VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT NULL,
  is_superuser BOOLEAN DEFAULT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- projects table
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  project_name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- api_keys table for API authentication
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  api_key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL,
  project_id INT NOT NULL REFERENCES projects (id),
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- chats table to store chat sessions
CREATE TABLE chats (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  user_id INT NOT NULL REFERENCES users (id),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- messages table to store chat messages
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  chat_id INT NOT NULL REFERENCES chats (id),
  role VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- chat project
CREATE TABLE chat_project (
  chat_id INT NOT NULL REFERENCES chats (id),
  project_id INT NOT NULL REFERENCES projects (id),
  PRIMARY KEY (chat_id, project_id)
);

-- document_uploads table for tracking file uploads
CREATE TABLE document_uploads (
  id SERIAL PRIMARY KEY,
  project_id INT NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  file_hash VARCHAR(64) NOT NULL,
  file_size BIGINT NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  temp_path VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  error_message TEXT,
  user_id INT NOT NULL REFERENCES users (id)
);

-- documents table for storing document information
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  file_path VARCHAR(255) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_size INT,
  content_type VARCHAR(100),
  file_hash VARCHAR(64),
  project_id INT NOT NULL REFERENCES projects (id),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  uploaded_by INT NOT NULL REFERENCES users (id),
  UNIQUE (project_id, file_name)
);

-- processing_tasks table for document processing
CREATE TABLE processing_tasks (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects (id),
  document_id INT REFERENCES documents (id),
  status VARCHAR(50),
  error_message TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  document_upload_id INT REFERENCES document_uploads (id),
  initiated_by INT REFERENCES users (id)
);

-- document_chunks table for storing document chunks for RAG
CREATE TABLE document_chunks (
  id VARCHAR(64) PRIMARY KEY,
  project_id INT NOT NULL REFERENCES projects (id),
  file_name VARCHAR(255) NOT NULL,
  hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  document_id INT NOT NULL REFERENCES documents (id),
  chunk_metadata JSON
);

-- Enhanced permissions table for role-based access control
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_system_level BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- project_permissions 
CREATE TABLE project_permissions (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    permission_id INT NOT NULL REFERENCES permissions (id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, user_id, permission_id)
);


