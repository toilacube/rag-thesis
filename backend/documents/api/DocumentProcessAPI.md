---
FILE: documents/api/DocumentProcessAPI.md
---
```markdown
# Document Processing API Documentation

**- All API endpoints have a prefix `/api` - e.g., `http://localhost:8000/api/document`**
**- All requests requiring authentication must include an `Authorization: Bearer YOUR_ACCESS_TOKEN` header.**

## Summary of Changes from Previous API

The document processing API has been significantly refactored to use an asynchronous processing model with RabbitMQ.

**Key Differences from the Old API:**

1.  **Removal of `/document/process` Endpoint:** Previously, document processing was a two-step process: first upload, then a separate call to `/document/process` with upload IDs to initiate processing. This endpoint is **no longer needed**.
2.  **Automatic Queuing:** Document processing is now automatically queued via RabbitMQ immediately after a successful upload through the `/document/upload` endpoint.
3.  **Status Code for Upload:** The `/document/upload` endpoint now returns a `202 ACCEPTED` status code, indicating the files have been accepted for asynchronous processing, rather than a `201 CREATED` implying immediate completion.
4.  **Simplified Status Tracking:** The `DocumentUpload` record itself now tracks the lifecycle (e.g., `queued`, `processing`, `completed`, `error`), making the `ProcessingTask` model obsolete.

The API is now more streamlined, providing a more responsive experience for file uploads and a more robust backend processing system.

## Current Document Processing API

### Base URL

All endpoints are prefixed with `/api`. For example, `http://localhost:8000/api/document`.

### Endpoints

#### 1. Upload Documents for Asynchronous Processing

**POST** `/document/upload`

Uploads one or more document files to a specified project. The files are validated, saved temporarily, and then a message is published to a RabbitMQ queue to trigger asynchronous processing (text extraction, chunking, embedding, and storage).

**Request Body:**

*   Form data:
    *   `files`: List of document files to upload (PDF, DOCX, DOC, TXT, MD, XLS, XLSX).
    *   `project_id`: ID of the project to upload the documents to.

**Curl Example:**
```bash
curl -X POST 'http://localhost:8000/api/document/upload' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -F 'files=@/path/to/your/file1.pdf' \
  -F 'files=@/path/to/your/file2.docx' \
  -F 'project_id=1'
```

**Success Response (`202 ACCEPTED`):**
A list of results, one for each attempted file upload.
```json
[
  {
    "file_name": "file1.pdf",
    "status": "queued", // Indicates successfully queued for processing
    "upload_id": 1,
    "document_id": null,
    "is_exist": false,
    "error": null
  },
  {
    "file_name": "existing_document.docx",
    "status": "exists", // Document with same content hash already processed for this project
    "upload_id": null,
    "document_id": 101, // ID of the existing processed document
    "is_exist": true,
    "error": null
  },
  {
    "file_name": "too_large.txt",
    "status": "error",
    "upload_id": null,
    "document_id": null,
    "is_exist": false,
    "error": "File size exceeds maximum allowed (50MB)"
  }
]
```
**`DocumentUploadResult` Fields:**
*   `file_name` (string): The name of the uploaded file.
*   `status` (string): The initial status of the upload attempt:
    *   `"queued"`: File validated and successfully sent to the processing queue.
    *   `"`exists`"`: A document with the same content hash already exists in the project. No new processing will occur.
    *   `"`error`"`: An error occurred during initial validation (e.g., file type, size) or when trying to queue the file.
*   `upload_id` (integer, optional): The ID of the `DocumentUpload` record created if the file was queued or an error occurred after record creation. Null if it was an "exists" case or pre-queue validation error.
*   `document_id` (integer, optional): If `status` is `"exists"`, this is the ID of the already processed `Document`.
*   `is_exist` (boolean): True if a document with the same content hash already exists for this project.
*   `error` (string, optional): An error message if the `status` is `"error"`.

---

#### 2. Test Document Processing with String Content

**POST** `/document/test-upload-string`

Accepts document content as a string, saves it to a temporary file, and queues it for asynchronous processing via RabbitMQ. This endpoint is primarily intended for testing the processing pipeline without actual file handling on the client-side.

**Request Body:** `DocumentUploadStringRequest` schema.
```json
{
  "project_id": 1,
  "file_name": "my_test_doc.md",
  "document_content": "# My Test Document\n\nThis is the content.",
  "content_type": "text/markdown"
}
```

**Curl Example:**
```bash
curl -X POST 'http://localhost:8000/api/document/test-upload-string' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "project_id": 1,
    "file_name": "test_from_string.txt",
    "document_content": "This is test content sent as a string.",
    "content_type": "text/plain"
  }'
```

**Success Response (`202 ACCEPTED`):**
A single `DocumentUploadResult` object.
```json
{
  "file_name": "test_from_string.txt",
  "status": "queued",
  "upload_id": 2,
  "document_id": null,
  "is_exist": false,
  "error": null
}
```
*(Response structure is the same as for `/document/upload` but for a single "file")*

---

#### 3. Get Document Upload Status

**GET** `/document/upload/status`

Retrieves the current processing status for a list of document uploads using their `upload_id`s.

**Query Parameters:**
*   `upload_ids` (List[int], required): A list of `DocumentUpload` IDs to check.
    *   Example: `?upload_ids=1&upload_ids=2&upload_ids=3`

**Curl Example:**
```bash
curl -X GET 'http://localhost:8000/api/document/upload/status?upload_ids=1&upload_ids=2' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

**Success Response (`200 OK`):**
A dictionary where keys are the requested `upload_id`s and values are `ProcessingStatusResponse` objects.
```json
{
  "1": {
    "upload_id": 1,
    "file_name": "file1.pdf",
    "upload_status": "completed", // Status from DocumentUpload record
    "upload_error": null,
    "document_id": 102 // ID of the processed Document if 'completed'
  },
  "2": {
    "upload_id": 2,
    "file_name": "file_being_processed.docx",
    "upload_status": "processing",
    "upload_error": null,
    "document_id": 103 // document_id might be set once Document record is created
  },
  "99": { // Example for an ID that was not found
    "status": "not_found",
    "detail": "DocumentUpload ID not found."
  }
}
```
**`ProcessingStatusResponse` Fields:**
*   `upload_id` (integer): The ID of the `DocumentUpload` record.
*   `file_name` (string): The original name of the uploaded file.
*   `upload_status` (string): The current status of this upload (e.g., `queued`, `processing`, `completed`, `error`).
*   `upload_error` (string, optional): Error message if `upload_status` is `error`.
*   `document_id` (integer, optional): The ID of the final `Document` record if processing is complete or the `Document` record has been created.

---

#### 4. Get Documents by Project ID with Processing Status

**GET** `/document/project/{project_id}/with-status`

Retrieves all document uploads associated with a specific project, along with their current processing status and details of the processed document if available.

**Path Parameters:**
*   `project_id` (integer, required): ID of the project.

**Curl Example:**
```bash
curl -X GET 'http://localhost:8000/api/document/project/1/with-status' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

**Success Response (`200 OK`):**
A list of `DocumentWithStatusResponse` objects.
```json
[
  {
    "id": 102, // Document ID (if processed)
    "file_path": "s3://your-bucket/project_1/hash123/file1.pdf",
    "file_name": "file1.pdf", // Original upload filename
    "file_size": 123456,
    "content_type": "application/pdf",
    "file_hash": "hash123...",
    "project_id": 1,
    "created_at": "2025-05-18T14:30:00Z", // Document creation time
    "updated_at": "2025-05-18T14:30:00Z",
    "uploaded_by": 123,
    "processing_status": "completed", // Derived from DocumentUpload status
    "error_message": null,
    "upload_id": 1 // Corresponding DocumentUpload ID
  },
  {
    "id": null, // No Document ID yet
    "file_path": null,
    "file_name": "file_in_queue.txt",
    "file_size": 5000,
    "content_type": "text/plain",
    "file_hash": "hash456...",
    "project_id": 1,
    "created_at": "2025-05-18T15:00:00Z", // DocumentUpload creation time
    "updated_at": "2025-05-18T15:00:00Z",
    "uploaded_by": 123,
    "processing_status": "queued",
    "error_message": null,
    "upload_id": 3
  }
]
```
**`DocumentWithStatusResponse` Fields:**
*   Many fields are from the `Document` record if processing is complete (`id`, `file_path`, etc.).
*   If processing is not yet complete or failed, these fields might be `null`, and information is taken from the `DocumentUpload` record (`file_name`, `file_size` from upload, etc.).
*   `processing_status` (string): The current lifecycle status of the upload (e.g., `queued`, `processing`, `completed`, `error`).
*   `error_message` (string, optional): Error message if processing failed.
*   `upload_id` (integer): The ID of the `DocumentUpload` entry this status pertains to.

### Other Document Endpoints (Unchanged by Processing Refactor)

These endpoints operate on **successfully processed documents** and their core functionality remains the same:

*   **`GET /document/{document_id}`**: Get a specific processed document by its ID.
*   **`GET /document/project/{project_id}`**: Get all processed documents for a project.
*   **`POST /document/search_chunks`**: Search for chunks within processed documents.

### File Type Support

The document upload endpoints support: PDF, DOCX, DOC, TXT, MD, XLS, XLSX.
Maximum file size: 50MB.

### Error Responses (General for Uploads)

*   `400 Bad Request`: Invalid input, unsupported file type, file too large.
*   `401 Unauthorized`: Missing or invalid authentication token.
*   `403 Forbidden`: User does not have permission (e.g., "add\_document" for the project).
*   `404 Not Found`: Project ID not found.
*   `500 Internal Server Error`: Unexpected server error during the synchronous part of the upload (e.g., failure to write temp file, initial DB error). Errors during asynchronous processing will be reflected in the `DocumentUpload` status.
```

