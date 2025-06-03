# Document Content API Endpoints

This document outlines the API endpoints for retrieving document content, specifically the extracted Markdown and the original uploaded file.

**Authentication**: All endpoints require a JWT Bearer token in the `Authorization` header.

---

## 1. Get Document Markdown Content

Retrieves the extracted/converted Markdown content for a specific document.

-   **Endpoint**: `GET /api/documents/{document_id}/markdown`
-   **Description**: Fetches the plain text Markdown representation of a processed document. This content is typically generated during the document ingestion process.
-   **Path Parameters**:
    -   `document_id` (integer, required): The ID of the document.
-   **Success Response**:
    -   **Code**: `200 OK`
    -   **Content-Type**: `text/plain; charset=utf-8`
    -   **Body**: The raw Markdown content as a string.
        ```markdown
        # Example Document Title

        This is a paragraph in the document.

        - List item 1
        - List item 2
        ```
-   **Error Responses**:
    -   `401 Unauthorized`: If the JWT token is missing or invalid.
    -   `403 Forbidden`: If the user does not have permission to view the project associated with the document.
    -   `404 Not Found`:
        -   If the document with the given `document_id` does not exist.
        -   If Markdown content is not available for the document (e.g., processing failed or link is missing).
        -   If the Markdown file (local or S3) is not found at the stored location.
    -   `500 Internal Server Error`: If there's an issue retrieving the content from storage (e.g., S3 misconfiguration, file read error).

---

## 2. Download Original Document File

Retrieves and streams the original uploaded document file.

-   **Endpoint**: `GET /api/documents/{document_id}/download`
-   **Description**: Allows downloading the original file that was uploaded for a specific document. The file is streamed to the client.
-   **Path Parameters**:
    -   `document_id` (integer, required): The ID of the document.
-   **Success Response**:
    -   **Code**: `200 OK`
    -   **Content-Type**: The original `Content-Type` of the uploaded file (e.g., `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`). Defaults to `application/octet-stream` if not available.
    -   **Headers**:
        -   `Content-Disposition: attachment; filename="your_document_name.ext"`: Suggests the original filename for download.
    -   **Body**: The binary content of the original file.
-   **Error Responses**:
    -   `401 Unauthorized`: If the JWT token is missing or invalid.
    -   `403 Forbidden`: If the user does not have permission to view/download the document (e.g., based on project permissions).
    -   `404 Not Found`:
        -   If the document with the given `document_id` does not exist.
        -   If the `file_path` for the document is not available.
        -   If the file is not found in S3 storage or at the specified local path.
    -   `500 Internal Server Error`: If there's an issue with S3 configuration or an unexpected error occurs while retrieving or streaming the file.

---