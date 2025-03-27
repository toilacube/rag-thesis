

-- users table for authentication and user management
CREATE TABLE users (
  id int NOT NULL AUTO_INCREMENT,
  email varchar(255) NOT NULL,
  username varchar(255) NOT NULL,
  hashed_password varchar(255) NOT NULL,
  is_active tinyint(1) DEFAULT NULL,
  is_superuser tinyint(1) DEFAULT NULL,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ix_users_email (email),
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- projects table
CREATE TABLE projects (
  id int NOT NULL AUTO_INCREMENT,
  project_name varchar(255) NOT NULL,
  description longtext,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  PRIMARY KEY (id),
  KEY ix_knowledge_bases_id (id)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- api_keys table for API authentication
CREATE TABLE api_keys (
  id int NOT NULL AUTO_INCREMENT,
  api_key varchar(128) NOT NULL,
  name varchar(255) NOT NULL,
  project_id int NOT NULL,
  is_active tinyint(1) NOT NULL,
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (project_id) REFERENCES projects (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- chats table to store chat sessions
CREATE TABLE chats (
  id int NOT NULL AUTO_INCREMENT,
  title varchar(255) NOT NULL,
  user_id int NOT NULL,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  PRIMARY KEY (id),
  KEY user_id (user_id),
  KEY ix_chats_id (id),
  CONSTRAINT chats_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- messages table to store chat messages
CREATE TABLE messages (
  id int NOT NULL AUTO_INCREMENT,
  chat_id int NOT NULL,
  role varchar(50) NOT NULL,
  content longtext NOT NULL,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  PRIMARY KEY (id),
  KEY chat_id (chat_id),
  KEY ix_messages_id (id),
  CONSTRAINT messages_ibfk_1 FOREIGN KEY (chat_id) REFERENCES chats (id)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- chat project
CREATE TABLE chat_project (
  chat_id int NOT NULL,
  project_id int NOT NULL,
  PRIMARY KEY (chat_id,project_id),
  KEY knowledge_base_id (project_id),
  FOREIGN KEY (chat_id) REFERENCES chats (id),
  FOREIGN KEY (project_id) REFERENCES projects (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- document_uploads table for tracking file uploads
CREATE TABLE document_uploads (
  id int NOT NULL AUTO_INCREMENT,
  project_id int NOT NULL,
  file_name varchar(255) NOT NULL,
  file_hash varchar(64) NOT NULL,
  file_size bigint NOT NULL,
  content_type varchar(100) NOT NULL,
  temp_path varchar(255) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status varchar(50) NOT NULL DEFAULT 'pending',
  error_message text,
  user_id int NOT NULL, -- Added to track who uploaded the document
  PRIMARY KEY (id),
  KEY knowledge_base_id (project_id),
  KEY ix_document_uploads_created_at (created_at),
  KEY ix_document_uploads_status (status),
  KEY ix_document_uploads_user_id (user_id),
  CONSTRAINT document_uploads_ibfk_1 FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
  CONSTRAINT document_uploads_ibfk_2 FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- documents table for storing document information
CREATE TABLE documents (
  id int NOT NULL AUTO_INCREMENT,
  file_path varchar(255) NOT NULL,
  file_name varchar(255) NOT NULL,
  file_size int DEFAULT NULL,
  content_type varchar(100) DEFAULT NULL,
  file_hash varchar(64) DEFAULT NULL,
  project_id int NOT NULL,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  uploaded_by int NOT NULL, -- Added to track who uploaded the document
  PRIMARY KEY (id),
  UNIQUE KEY uq_kb_file_name (project_id,file_name),
  KEY ix_documents_file_hash (file_hash),
  KEY ix_documents_id (id),
  KEY ix_documents_uploaded_by (uploaded_by),
  CONSTRAINT documents_ibfk_1 FOREIGN KEY (project_id) REFERENCES projects (id),
  CONSTRAINT documents_ibfk_2 FOREIGN KEY (uploaded_by) REFERENCES users (id)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- processing_tasks table for document processing
CREATE TABLE processing_tasks (
  id int NOT NULL AUTO_INCREMENT,
  project_id int DEFAULT NULL,
  document_id int DEFAULT NULL,
  status varchar(50) DEFAULT NULL,
  error_message text,
  created_at datetime DEFAULT NULL,
  updated_at datetime DEFAULT NULL,
  document_upload_id int DEFAULT NULL,
  initiated_by int DEFAULT NULL, -- Added to track who initiated the processing task
  PRIMARY KEY (id),
  KEY document_id (document_id),
  KEY processing_tasks_document_upload_id_fkey (document_upload_id),
  KEY processing_tasks_initiated_by_fkey (initiated_by),
  CONSTRAINT processing_tasks_document_upload_id_fkey FOREIGN KEY (document_upload_id) REFERENCES document_uploads (id),
  CONSTRAINT processing_tasks_ibfk_1 FOREIGN KEY (document_id) REFERENCES documents (id),
  CONSTRAINT processing_tasks_ibfk_2 FOREIGN KEY (project_id) REFERENCES projects (id),
  CONSTRAINT processing_tasks_ibfk_3 FOREIGN KEY (initiated_by) REFERENCES users (id)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- document_chunks table for storing document chunks for RAG
CREATE TABLE document_chunks (
  id varchar(64) NOT NULL,
  project_id int NOT NULL,
  file_name varchar(255) NOT NULL,
  hash varchar(64) NOT NULL,
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  document_id int NOT NULL,
  chunk_metadata json DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_kb_file_name (project_id,file_name),
  KEY ix_document_chunks_hash (hash),
  KEY document_id (document_id),
  CONSTRAINT document_chunks_ibfk_1 FOREIGN KEY (project_id) REFERENCES projects (id),
  CONSTRAINT document_chunks_ibfk_2 FOREIGN KEY (document_id) REFERENCES documents (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Enhanced permissions table for role-based access control
CREATE TABLE permissions (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_system_level BOOLEAN NOT NULL DEFAULT FALSE, -- Flag for system-level permissions vs project-level
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY ix_permissions_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- project_permissions 
CREATE TABLE project_permissions (
    id INT NOT NULL AUTO_INCREMENT,
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_user_permission (project_id, user_id, permission_id),
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


