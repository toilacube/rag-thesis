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
} from "react-icons/fi"; // Added icons
import { api, ApiError } from "@/lib/api";

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

export function DocumentList({ projectId }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentWithStatus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        // Use the new endpoint to get documents with their processing status
        const data = await api.get(
          `/api/document/project/${projectId}/with-status`,
        );
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
          <Badge variant="default" className="bg-blue-100 text-blue-700">
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
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Uploaded/Created</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Details</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow key={doc.upload_id}>
            {" "}
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
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
