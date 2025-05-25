// Relevant for document-upload-steps.tsx and document-list.tsx

// From: POST /api/document/upload (Array of these)
export interface DocumentUploadResult {
  file_name: string;
  status: "queued" | "exists" | "error";
  upload_id: number | null;
  document_id: number | null; // If status is "exists"
  is_exist: boolean;
  error: string | null;
}

// From: GET /api/document/upload/status (Value in the map for each upload_id)
export interface ProcessingStatusDetail {
  upload_id: number;
  file_name: string;
  upload_status: "queued" | "processing" | "completed" | "error" | "not_found";
  upload_error: string | null;
  document_id: number | null; // If processing led to a Document record
}

// The overall response type for GET /api/document/upload/status
export type ProcessingStatusResponseMap = Record<
  string,
  ProcessingStatusDetail | { status: "not_found"; detail: string }
>;

// From: GET /api/document/project/{project_id}/with-status (Array of these)
// This will be used in document-list.tsx, replacing the old Document interface
export interface DocumentWithStatus {
  id: number | null; // Document ID (if processed, else null)
  file_path: string | null;
  file_name: string; // Original upload filename
  file_size: number | null;
  content_type: string | null;
  file_hash: string | null;
  project_id: number;
  created_at: string; // ISO Date string
  updated_at: string; // ISO Date string
  uploaded_by: number | null; // User ID, might be null
  processing_status: "queued" | "processing" | "completed" | "error" | string; // Using string for flexibility if backend adds more
  error_message: string | null;
  upload_id: number; // Corresponding DocumentUpload ID
}

// Updated UI state for files in document-upload-steps.tsx
export interface UploadFileStatus {
  id: string; // Unique ID for UI key, e.g., file.name + file.lastModified
  file: File;
  uiStatus:
    | "pending_selection"
    | "uploading_to_server"
    | "awaits_processing" // "queued" from API
    | "processing_on_server" // "processing" from polling API
    | "completed_success" // "completed" from polling API
    | "completed_exists" // "exists" from API
    | "failed_upload" // Error from initial /document/upload API call
    | "failed_processing"; // "error" from API or polling
  serverUploadId: number | null;
  serverDocumentId: number | null;
  errorMessage: string | null;
  progress?: number; // For displaying HTTP upload progress (0-100), optional
}
