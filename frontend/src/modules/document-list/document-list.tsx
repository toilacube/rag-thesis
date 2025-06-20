"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/badge";
import { formatDistanceToNow } from "date-fns";
import { FileIcon, defaultStyles } from "react-file-icon";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/table";
import {
  FiAlertCircle,
  FiCheckCircle,
  FiClock,
  FiLoader,
  FiFileText,
  FiHelpCircle,
  FiDownload,
  FiEye,
} from "react-icons/fi"; // Added icons
// import { api, ApiError } from "@/lib/api"; // No longer using client-side api for these
import { ApiError } from "@/lib/api"; // Keep for error instance checking if needed, or remove if server actions handle errors fully
import { getDocumentList } from "./utils/get-document-list";
import { downloadDocumentAction } from "./utils/download-document";
import { previewDocumentAction } from "./utils/preview-document";

// --- START: TypeScript Interfaces (can be moved to a types file) ---
export interface DocumentWithStatus {
  id: number | null; // Document ID (if processed, else null)
  file_path: string | null;
  file_name: string; // Original upload filename
  file_size: number | null;
  content_type: string | null;
  file_hash: string | null;
  project_id: number;
  created_at: string; // ISO Date string from DocumentUpload or Document
  updated_at: string;
  uploaded_by: number | null;
  processing_status: "queued" | "processing" | "completed" | "error" | string;
  error_message: string | null;
  upload_id: number; // Corresponding DocumentUpload ID
}
// --- END: TypeScript Interfaces ---

interface DocumentListProps {
  projectId: number;
}

const DocumentList = ({ projectId }: DocumentListProps) => {
  const [documents, setDocuments] = useState<DocumentWithStatus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewMarkdown, setPreviewMarkdown] = useState<string | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        const data = await getDocumentList(projectId);
        setDocuments(data as DocumentWithStatus[]);
        setError(null);
      } catch (error) {
        console.error("Failed to fetch documents:", error);
        if (error instanceof ApiError) {
          setError(error.message);
        } else {
          setError("Failed to fetch documents. Please try again later.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      // Ensure projectId is valid before fetching
      fetchDocuments();
    } else {
      setLoading(false);
      setError("Project ID is not available.");
    }
  }, [projectId]);

  const handleDownload = async (doc: DocumentWithStatus) => {
    if (!doc.id) {
      console.error("Document ID is missing, cannot download.");
      // Optionally, show a toast notification to the user
      alert("Document ID is missing. Cannot download.");
      return;
    }
    try {
      const result = await downloadDocumentAction(doc.id);
      if (result.success && result.data && result.contentType) {
        const byteCharacters = atob(result.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: result.contentType });

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = doc.file_name || "download";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        console.error("Failed to download document:", result.message);
        alert(`Download error: ${result.message || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Failed to download document (exception):", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to download document.";
      alert(`Download error: ${errorMessage}`);
    }
  };

  const handlePreview = async (doc: DocumentWithStatus) => {
    if (!doc.id) {
      console.error("Document ID is missing, cannot preview.");
      alert("Document ID is missing. Cannot preview.");
      return;
    }
    try {
      const result = await previewDocumentAction(doc.id);

      setPreviewMarkdown(result.markdown);
      setShowPreviewModal(true);
    } catch (err) {
      console.error("Failed to fetch markdown for preview (exception):", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load preview.";
      alert(`Preview error: ${errorMessage}`);
      setPreviewMarkdown(null);
      setShowPreviewModal(false);
    }
  };

  const getStatusBadge = (status: DocumentWithStatus["processing_status"]) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-700">
            <FiCheckCircle className="mr-1 inline" /> Completed
          </Badge>
        );
      case "processing":
        return (
          <Badge variant="default" className="bg-gray-100 text-gray-700">
            <FiLoader className="mr-1 inline animate-spin" /> Processing
          </Badge>
        );
      case "queued":
        return (
          <Badge variant="outline" className="bg-yellow-100 text-yellow-700">
            <FiClock className="mr-1 inline" /> Queued
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive">
            <FiAlertCircle className="mr-1 inline" /> Error
          </Badge>
        );
      default: // Covers null, undefined, or other unexpected statuses
        return (
          <Badge variant="outline">
            <FiHelpCircle className="mr-1 inline" /> Unknown
          </Badge>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="space-y-4">
          <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto"></div>
          <p className="text-muted-foreground animate-pulse">
            Loading documents...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center p-8">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[200px] p-8 border rounded-lg bg-card">
        <div className="flex flex-col items-center max-w-[420px] text-center space-y-6">
          <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
            <FiFileText className="w-10 h-10 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-semibold">No documents yet</h3>
            <p className="text-muted-foreground">
              Upload your first document to start building your knowledge base
              for this project.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Uploaded/Created</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Details</TableHead>
            <TableHead className="text-center">Download</TableHead>
            <TableHead className="text-center">Preview</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.upload_id}>
              {/* Use upload_id as key as doc.id can be null */}
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 flex-shrink-0">
                    <FileIcon
                      extension={
                        doc.file_name.split(".").pop()?.toLowerCase() || ""
                      }
                      {...defaultStyles[
                        doc.file_name
                          .split(".")
                          .pop()
                          ?.toLowerCase() as keyof typeof defaultStyles
                      ]}
                      color="#E2E8F0" // Default color if type not in defaultStyles
                      labelColor="#94A3B8"
                    />
                  </div>
                  <span className="truncate" title={doc.file_name}>
                    {doc.file_name}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                {doc.file_size
                  ? `${(doc.file_size / 1024 / 1024).toFixed(2)} MB`
                  : "N/A"}
              </TableCell>
              <TableCell>
                {formatDistanceToNow(new Date(doc.created_at), {
                  // created_at is from DocumentUpload initially, then Document
                  addSuffix: true,
                })}
              </TableCell>
              <TableCell>{getStatusBadge(doc.processing_status)}</TableCell>
              <TableCell>
                {doc.processing_status === "error" && doc.error_message && (
                  <p
                    className="text-xs text-destructive truncate"
                    title={doc.error_message}
                  >
                    {doc.error_message}
                  </p>
                )}
                {doc.id && doc.processing_status === "completed" && (
                  <p className="text-xs text-muted-foreground">
                    Doc ID: {doc.id}
                  </p>
                )}
              </TableCell>
              <TableCell className="text-center">
                <button
                  onClick={() => handleDownload(doc)}
                  title="Download document"
                  className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
                  disabled={!doc.id || doc.processing_status !== "completed"}
                >
                  <FiDownload size={18} />
                </button>
              </TableCell>
              <TableCell className="text-center">
                <button
                  onClick={() => handlePreview(doc)}
                  title="Preview document"
                  className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
                  disabled={!doc.id || doc.processing_status !== "completed"}
                >
                  <FiEye size={18} />
                </button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {showPreviewModal && previewMarkdown && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowPreviewModal(false)}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "20px",
              borderRadius: "8px",
              maxWidth: "80%",
              maxHeight: "80%",
              overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
          >
            <h3 style={{ marginTop: 0 }}>Document Preview</h3>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                wordWrap: "break-word",
                maxHeight: "60vh",
                overflowY: "auto",
                border: "1px solid #ccc",
                padding: "10px",
                borderRadius: "4px",
                background: "#f9f9f9",
              }}
            >
              {previewMarkdown}
            </pre>
            <button
              onClick={() => setShowPreviewModal(false)}
              style={{ marginTop: "10px" }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentList;
