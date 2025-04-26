"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  FiUpload,
  FiX,
  FiFileText,
  FiCheckCircle,
  FiAlertCircle,
  FiLoader,
} from "react-icons/fi";

interface FileStatus {
  file: File;
  status:
    | "pending"
    | "uploading"
    | "uploaded"
    | "processing"
    | "completed"
    | "error";
  error?: string;
  uploadId?: number;
  taskId?: number;
  documentId?: number;
}

interface UploadResult {
  upload_id?: number;
  document_id?: number;
  file_name: string;
  status: string;
  skip_processing: boolean;
  message?: string;
}

interface ProcessingTask {
  upload_id: number;
  task_id: number;
}

interface TaskStatus {
  document_id: number | null;
  status: string;
  error_message: string | null;
  upload_id: number;
  file_name: string;
}

export default function UploadPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [files, setFiles] = useState<FileStatus[]>([]);
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      status: "pending" as const,
    }));
    setFiles((prev) => [...prev, ...newFiles]);

    // Upload each file
    newFiles.forEach(async (fileStatus) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === fileStatus.file ? { ...f, status: "uploading" } : f
        )
      );
      await handleUpload(fileStatus.file);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/plain": [".txt"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "text/markdown": [".md"],
    },
  });

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
  };

  const startProcessing = async () => {
    const uploadedFiles = files.filter((f) => f.status === "uploaded");
    if (uploadedFiles.length === 0) return;

    setIsProcessing(true);
  };

  const checkProcessingStatus = async () => {
    if (processingTasks.length === 0) return;
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isProcessing) {
      interval = setInterval(checkProcessingStatus, 2000);
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isProcessing, processingTasks]);

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const allCompleted =
    files.length > 0 &&
    files.every((f) => f.status === "completed" || f.status === "error");

  const hasUploadedFiles = files.some((f) => f.status === "uploaded");
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Upload Documents</h2>
        <p className="text-muted-foreground">
          Upload documents to your knowledge base
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
        }`}
      >
        <input {...getInputProps()} />
        <FiUpload className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-4 text-sm text-muted-foreground">
          Drag and drop files here, or click to select files
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Supported formats: PDF, DOCX, TXT, MD
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Files</h3>
            {hasUploadedFiles && !isProcessing && (
              <button
                onClick={startProcessing}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
                Start Processing
              </button>
            )}
          </div>

          <div className="space-y-2 max-h-[400px] overflow-y-auto rounded-lg">
            {files.map((fileStatus) => (
              <div
                key={fileStatus.file.name}
                className="flex items-center justify-between p-4 rounded-lg border bg-card"
              >
                <div className="flex items-center space-x-4">
                  <FiFileText className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium">{fileStatus.file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(fileStatus.file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {fileStatus.status === "uploading" && (
                    <div className="flex items-center space-x-2">
                      <FiLoader className="h-4 w-4 animate-spin" />
                      <span className="text-muted-foreground">
                        Uploading...
                      </span>
                    </div>
                  )}
                  {fileStatus.status === "processing" && (
                    <div className="flex items-center space-x-2">
                      <FiLoader className="h-4 w-4 animate-spin" />
                      <span className="text-muted-foreground">
                        Processing...
                      </span>
                    </div>
                  )}
                  {fileStatus.status === "completed" && (
                    <FiCheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {fileStatus.status === "error" && (
                    <div className="flex items-center space-x-2 text-red-500">
                      <FiAlertCircle className="h-5 w-5" />
                      <span className="text-sm">{fileStatus.error}</span>
                    </div>
                  )}
                  <button
                    onClick={() => removeFile(fileStatus.file)}
                    className="p-1 hover:bg-accent rounded-full"
                  >
                    <FiX className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end space-x-4">
        {showSuccessModal ? (
          <button
            onClick={() => router.push(`/dashboard/project/${params.id}`)}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            Done
          </button>
        ) : (
          <button
            onClick={() => router.push(`/dashboard/project/${params.id}`)}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
