## Setup 
- To setup the backend please see README.md in `./backend` directory

# Document Chat System Architecture

This document provides an overview of the RAG (Retrieval-Augmented Generation) system architecture and explains how the document processing task queue works.

## System Overview

The system is a Retrieval-Augmented Generation (RAG) application that allows users to:

1. Create and manage projects
2. Upload and process documents
3. Chat with an AI assistant using the uploaded documents as context
4. Manage permissions across different projects

## Database Schema and Relationships

The system is built on a robust relational database model with the following key entities:

### Core Entities

```mermaid
erDiagram
    USER ||--o{ PROJECT : "manages"
    USER ||--o{ CHAT : "initiates"
    USER ||--|| DOCUMENT : "uploads"
    PROJECT ||--o{ DOCUMENT : "contains"
    PROJECT ||--o{ DOCUMENT_CHUNK : "references"
    DOCUMENT ||--o{ DOCUMENT_CHUNK : "has"
    CHAT ||--o{ MESSAGE : "contains"
    CHAT }o--|| PROJECT : "references"
```

### Key Entity Descriptions

- **User**: Authentication and user management
- **Project**: Container for documents and chats within a specific knowledge domain
- **Document**: Represents an uploaded file with metadata
- **DocumentChunk**: Smaller segments of documents used for retrieval
- **Chat**: Conversation session between a user and the AI
- **Message**: Individual messages within a chat
- **Permission**: Access controls for different actions
- **ProjectPermission**: User permissions for specific projects

## Document Processing Workflow

The system implements a robust document processing pipeline to handle document uploads, processing, and chunking for RAG applications.

### Document Upload and Processing Flow

```mermaid
sequenceDiagram
    %% Color definitions
    participant User as User<br>(Actor)
    participant API as API<br>(System)
    participant DocumentUpload as Document Upload<br>(Service)
    participant ProcessingTask as Processing Task<br>(Worker)
    participant Document as Document<br>(Database)
    participant DocumentChunk as Chunks<br>(Vector DB)

    %% Color application
    rect rgba(255,154,60,0.1)
    User->>API: Upload document
    end

    rect rgba(22,109,103,0.1)
    API->>DocumentUpload: Create entry (status: pending)
    API->>User: Confirm upload received
    end

    rect rgba(58,134,255,0.1)
    API->>ProcessingTask: Create processing task
    ProcessingTask->>DocumentUpload: Update status (processing)
    end

    rect rgba(131,56,236,0.1)
    ProcessingTask->>Document: Process document
    Document->>DocumentChunk: Create chunks
    end

    rect rgba(255,0,110,0.1)
    ProcessingTask->>DocumentUpload: Update status (completed)
    end

    %% Legend
    Note right of User: Color Legend:<br>User Actions: Orange<br>Initial Processing: Teal<br>Document Handling: Blue<br>Chunking: Purple<br>Completion: Pink
```

## Task Queue Architecture

The document processing task queue is implemented using the following models:

### Document Processing Pipeline

```mermaid
flowchart TD
    %% Color scheme
    classDef upload fill:#ff9a3c,stroke:#333
    classDef validation fill:#ffbe0b,stroke:#333
    classDef processing fill:#3a86ff,stroke:#333
    classDef error fill:#ff006e,stroke:#333
    classDef storage fill:#8338ec,stroke:#333

    A[User uploads document]:::upload --> B[DocumentUpload created]:::upload
    B --> C{Initial validation}:::validation
    C -->|Valid| D[ProcessingTask created]:::processing
    C -->|Invalid| E[DocumentUpload status: error]:::error
    D --> F[Document processing]:::processing
    F --> G[Text extraction]:::processing
    G --> H[Document chunking]:::processing
    H --> I[Embedding generation]:::storage
    I --> J[Store in database]:::storage
    J --> K[ProcessingTask status: completed]:::processing
    F -->|Error| L[ProcessingTask status: error]:::error
    L --> M[DocumentUpload status: error]:::error

    %% Legend
    subgraph Legend
        direction TB
        upload[Upload]:::upload
        validation[Validation]:::validation
        processing[Processing]:::processing
        storage[Storage]:::storage
        error[Error]:::error
    end
```

## Models in Detail

### DocumentUpload

The `DocumentUpload` model represents the initial file upload and tracks its processing status:

- **Status**: pending → processing → completed/error
- **Fields**: project_id, file_name, file_hash, file_size, content_type, temp_path
- **Relationships**: Links to Project, User, and ProcessingTask

### ProcessingTask

The `ProcessingTask` model represents an asynchronous processing job for document handling:

- **Status**: pending → processing → completed/error
- **Fields**: project_id, document_id, status, error_message
- **Relationships**: Links to DocumentUpload, Document, and Project

### Document

The `Document` model represents a successfully processed document:

- **Fields**: file_path, file_name, project_id, uploaded_by
- **Relationships**: Links to User, Project, DocumentChunks
- **Document Types**:
  - **Stakeholder**: Documents that define project stakeholders, their roles, responsibilities, and contact information
  - **Requirements**: Documents that specify functional and non-functional requirements for the project
  - **Core Objective**: Documents that outline the main goals, mission statements, and strategic objective
  - **UI Story Board**: 

### DocumentChunk

The `DocumentChunk` model represents the individual searchable segments of a document:

- **Fields**: id (unique chunk identifier), project_id, document_id, hash, chunk_metadata (contains embedding vector)
- **Relationships**: Links to Document and Project

## Typical RAG Workflow

1. **Document Upload**: User uploads a document to a project
2. **Processing Queue**:
   - Document is validated and a DocumentUpload record is created
   - A ProcessingTask is created to handle the asynchronous processing
   - The document is processed (text extraction, chunking, embedding)
   - Chunks are stored with their embeddings for retrieval
3. **Chat and Retrieval**:
   - User asks a question in a chat
   - System retrieves relevant document chunks based on semantic similarity
   - Retrieved context is combined with the question and sent to LLM
   - LLM generates an answer with citations from the source documents
4. **Response Rendering**: The answer is displayed with proper citations and references

## Permission System

The system includes a comprehensive permission model:

- System-level permissions for admin functions
- Project-level permissions for fine-grained access control
- Permissions include: view_project, edit_project, add_document, delete_document, etc.

This allows organizations to implement appropriate access controls for their document knowledge bases.
