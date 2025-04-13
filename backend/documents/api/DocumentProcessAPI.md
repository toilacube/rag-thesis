# Document Processing API Documentation

**- All the api will have a prefix /api - http://localhost:8000/api**

## Document Processing API

### Base URL

All endpoints are prefixed with `/api`. For example, `http://localhost:8000/api/document`.

### Endpoints

#### 1. Upload and Process Documents

**POST** `/document/upload`

Uploads and processes multiple document files for a project. The files will be validated, saved, and queued for asynchronous processing.

**Request Body:**

- Form data:
  - `files`: List of document files to upload (PDF, DOCX, DOC, TXT, MD, XLS, XLSX)
  - `project_id`: ID of the project to upload the documents to

**Curl Example:**

```bash
curl -X POST http://localhost:8000/api/document/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "files=@/path/to/your/file1.pdf" \
  -F "files=@/path/to/your/file2.docx" \
  -F "project_id=1"
```

**Response:**

```json
[
  {
    "file_name": "file1.pdf",
    "status": "pending",
    "upload_id": 1,
    "is_exist": false
  },
  {
    "file_name": "file2.docx",
    "status": "exists",
    "document_id": 2,
    "upload_id": null,
    "is_exist": true
  },
  {
    "file_name": "file3.txt",
    "status": "error",
    "error": "File size exceeds maximum allowed (50MB)",
    "upload_id": null,
    "is_exist": false
  }
]
```

**Status Values:**

- `pending`: Document has been validated and queued for processing
- `exists`: Document with the same hash already exists in the project
- `error`: Error occurred during validation or upload

---

#### 2. Get Document Processing Status

**GET** `/document/upload/status`

Retrieves the processing status for a list of document uploads.

**Query Parameters:**

- `upload_ids`: List of document upload IDs to check (comma-separated)

**Curl Example:**

```bash
curl -X GET "http://localhost:8000/api/document/upload/status?upload_ids=1,2,3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
{
  "1": {
    "status": "completed",
    "file_name": "document1.pdf",
    "task_id": 1,
    "task_status": "completed",
    "document_id": 1
  },
  "2": {
    "status": "processing",
    "file_name": "document2.docx",
    "task_id": 2,
    "task_status": "processing"
  },
  "3": {
    "status": "error",
    "file_name": "invalid.xyz",
    "error": "Unsupported file type: application/octet-stream",
    "task_id": 3,
    "task_status": "error"
  }
}
```

**Status Values:**

- `pending`: Document is waiting to be processed
- `processing`: Document is currently being processed
- `completed`: Document has been successfully processed
- `error`: Error occurred during processing
- `not_found`: Specified upload ID was not found

---

#### 3. Get Documents with Processing Status

**GET** `/document/project/{project_id}/with-status`

Retrieves all documents for a project along with their processing status.

**Path Parameters:**

- `project_id`: ID of the project to get documents for

**Curl Example:**

```bash
curl -X GET "http://localhost:8000/api/document/project/1/with-status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
[
  {
    "id": 1,
    "file_path": "s3://documents/project_1/a1b2c3d4e5f6.../sample.pdf",
    "file_name": "sample.pdf",
    "file_size": 123456,
    "content_type": "application/pdf",
    "file_hash": "a1b2c3d4e5f6...",
    "project_id": 1,
    "created_at": "2025-04-13T10:30:00",
    "updated_at": "2025-04-13T10:30:00",
    "uploaded_by": 1,
    "processing_status": "completed",
    "error_message": null
  },
  {
    "id": 2,
    "file_path": "s3://documents/project_1/g7h8i9j0k1l2.../report.docx",
    "file_name": "report.docx",
    "file_size": 234567,
    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_hash": "g7h8i9j0k1l2...",
    "project_id": 1,
    "created_at": "2025-04-13T11:45:00",
    "updated_at": "2025-04-13T11:45:00",
    "uploaded_by": 1,
    "processing_status": "error",
    "error_message": "Error in document chunking: Invalid document format"
  }
]
```

### Processing Workflow

The document processing follows this sequence:

1. **Upload Phase**:

   - Document files are uploaded to the server
   - Each file is validated for format and size
   - A `DocumentUpload` record is created with status "pending"
   - Upload results are returned to the client immediately

2. **Processing Phase** (asynchronous):

   - A `ProcessingTask` is created for each valid upload
   - The task status is set to "processing"
   - The document is stored permanently (local filesystem or S3/MinIO)
   - A `Document` record is created with the permanent file path
   - The processor performs chunking and embedding generation (see CHUNKING.md)
   - The task status is updated to "completed" when finished

3. **Status Checking**:
   - Clients can check processing status using the upload IDs
   - Completed documents can be retrieved via document endpoints

### Error Responses

**400 Bad Request**

- When an unsupported file type is uploaded
- When file size exceeds maximum allowed (50MB)
- When required parameters are missing

**403 Forbidden**

- When the user doesn't have the required permission for the project

**404 Not Found**

- When a document, project, or upload ID cannot be found

**500 Internal Server Error**

- When an unexpected error occurs during document processing
