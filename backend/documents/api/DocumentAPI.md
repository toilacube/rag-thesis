# Document API Documentation

**- All the api will have a prefix /api - http://localhost:8000/api**

## Document API

### Base URL

All endpoints are prefixed with `/api`. For example, `http://localhost:8000/api/document`.

### Endpoints

#### 1. Upload a Document

**POST** `/document/upload`

Uploads a document file to a specified project. The file will be validated, saved, and queued for processing.

**Request Body:**

- Form data:
  - `file`: The document file to upload (PDF, DOCX, DOC, TXT, MD, XLS, XLSX)
  - `project_id`: ID of the project to upload the document to

**Curl Example:**

```bash
curl -X POST http://localhost:8000/api/document/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/file.pdf" \
  -F "project_id=1"
```

**Response:**

```json
{
  "id": 1,
  "project_id": 1,
  "file_name": "sample.pdf",
  "file_size": 123456,
  "content_type": "application/pdf",
  "file_hash": "a1b2c3d4e5f6...",
  "status": "completed",
  "created_at": "2025-04-13T10:30:00",
  "error_message": null
}
```

---

#### 2. Get Document by ID

**GET** `/document/{document_id}`

Retrieves document information by its ID.

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/document/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
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
  "uploaded_by": 1
}
```

---

#### 3. Get Documents by Project ID

**GET** `/document/project/{project_id}`

Retrieves all documents belonging to a project.

**Curl Example:**

```bash
curl -X GET http://localhost:8000/api/document/project/1 \
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
    "uploaded_by": 1
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
    "uploaded_by": 1
  }
]
```

### File Type Support

The document upload endpoint supports the following file types:

- PDF (application/pdf)
- Word Documents (DOCX, DOC)
- Text files (TXT)
- Markdown files (MD)
- Excel files (XLS, XLSX)

### Error Responses

**400 Bad Request**

- When an unsupported file type is uploaded
- When file size exceeds maximum allowed (50MB)

**404 Not Found**

- When a document or project cannot be found

**409 Conflict**

- When attempting to upload a document that already exists in the project

**500 Internal Server Error**

- When an unexpected error occurs during document upload or processing
