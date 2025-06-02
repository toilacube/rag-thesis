"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { FileIcon, defaultStyles } from "react-file-icon";
import { Button } from "@/components/button";
import { Card } from "@/components/card";
import { useToast } from "@/components/use-toast";
import {
  FiLoader,
  FiUpload,
  FiX,
  FiCheckCircle,
  FiAlertCircle,
  FiClock,
  FiHelpCircle,
} from "react-icons/fi";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api";
import { useDropzone } from "react-dropzone";
import { Badge } from "@/components/badge";
import { getStatusDocument } from "./utils/get-status-document";
import { uploadDocument } from "./utils/upload-document";

interface DocumentUploadStepsProps {
  projectId: number;
  onComplete?: () => void;
}

const DocumentUploadSteps = ({
  projectId,
  onComplete,
}: DocumentUploadStepsProps) => {
  const [files, setFiles] = useState<UploadFileStatus[]>([]);
  const [isUploading, setIsUploading] = useState(false); // For the initial POST /upload
  const { toast } = useToast();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [isPollingActive, setIsPollingActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFileStatuses: UploadFileStatus[] = acceptedFiles.map((file) => ({
      id: `${file.name}-${file.lastModified}`, // Simple unique ID
      file,
      uiStatus: "pending_selection" as const,
      serverUploadId: null,
      serverDocumentId: null,
      errorMessage: null,
      progress: 0,
    }));
    setFiles((prev) => {
      // Avoid duplicates if user drops same file again
      const existingIds = new Set(prev.map((f) => f.id));
      return [
        ...prev,
        ...newFileStatuses.filter((nf) => !existingIds.has(nf.id)),
      ];
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "application/msword": [".doc"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
  });

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleUploadAndInitiateProcessing = async () => {
    const filesToUpload = files.filter(
      (f) => f.uiStatus === "pending_selection",
    );
    if (filesToUpload.length === 0) return;

    setIsUploading(true);
    setFiles((prev) =>
      prev.map((f) =>
        f.uiStatus === "pending_selection"
          ? { ...f, uiStatus: "uploading_to_server", progress: 10 }
          : f,
      ),
    );

    try {
      const formData = new FormData();
      filesToUpload.forEach((fileStatus) => {
        formData.append("files", fileStatus.file);
      });
      formData.append("project_id", projectId.toString());

      // Note: Axios or another library could provide upload progress
      // For fetch, progress tracking is more involved. Assuming quick local uploads for now.
      // If you need progress, you'd use XHR or a library.
      // For simplicity, we'll just mark it as fully "uploading".

      const results = (await uploadDocument(formData)) as DocumentUploadResult[];

      let allUploadsSuccessfulOrExist = true;
      let hasQueuedFiles = false;

      setFiles((prevFiles) =>
        prevFiles.map((fs) => {
          if (fs.uiStatus !== "uploading_to_server") return fs; // Only update files that were part of this batch

          const result = results.find((r) => r.file_name === fs.file.name);
          if (result) {
            let newUiStatus: UploadFileStatus["uiStatus"] = fs.uiStatus;
            if (result.status === "queued") {
              newUiStatus = "awaits_processing";
              hasQueuedFiles = true;
            } else if (result.status === "exists") {
              newUiStatus = "completed_exists";
            } else if (result.status === "error") {
              newUiStatus = "failed_processing"; // Or "failed_upload" if more granular
              allUploadsSuccessfulOrExist = false;
            }
            return {
              ...fs,
              uiStatus: newUiStatus,
              serverUploadId: result.upload_id,
              serverDocumentId: result.document_id,
              errorMessage: result.error,
              progress: 100, // Upload to server complete
            };
          }
          // If a file was in uploading_to_server state but no result, mark as error
          allUploadsSuccessfulOrExist = false;
          return {
            ...fs,
            uiStatus: "failed_upload",
            errorMessage: "Upload result missing from server response.",
            progress: 100,
          };
        }),
      );

      if (allUploadsSuccessfulOrExist) {
        toast({
          title: "Uploads Accepted",
          description: `${results.length} files submitted. Processing will continue in the background.`,
        });
      } else {
        toast({
          title: "Some Uploads Had Issues",
          description: "Check file statuses below for details.",
          variant: "destructive",
        });
      }

      if (hasQueuedFiles) {
        startPolling();
      } else {
        // If no files were queued (all exist or errored immediately), check if onComplete can be called
        checkIfAllDone();
      }
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.uiStatus === "uploading_to_server"
            ? {
                ...f,
                uiStatus: "failed_upload",
                errorMessage:
                  error instanceof ApiError
                    ? error.message
                    : "Network error or server issue during upload.",
              }
            : f,
        ),
      );
      toast({
        title: "Upload Failed",
        description:
          error instanceof ApiError ? error.message : "Could not reach server.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const pollUploadStatus = async () => {
    const idsToPoll = files
      .filter(
        (f) =>
          (f.uiStatus === "awaits_processing" ||
            f.uiStatus === "processing_on_server") &&
          f.serverUploadId !== null,
      )
      .map((f) => f.serverUploadId!);

    if (idsToPoll.length === 0) {
      stopPolling();
      checkIfAllDone();
      return;
    }

    setIsPollingActive(true); // Keep polling active

    try {
      const queryParams = new URLSearchParams();
      idsToPoll.forEach((id) =>
        queryParams.append("upload_ids", id.toString()),
      );

      const statusMap = (await getStatusDocument(queryParams)) as ProcessingStatusResponseMap;

      setFiles((prevFiles) =>
        prevFiles.map((fs) => {
          if (!fs.serverUploadId || !idsToPoll.includes(fs.serverUploadId))
            return fs;

          const statusDetail = statusMap[fs.serverUploadId.toString()];
          if (statusDetail) {
            if (
              "status" in statusDetail &&
              statusDetail.status === "not_found"
            ) {
              return {
                ...fs,
                uiStatus: "failed_processing",
                errorMessage:
                  statusDetail.detail || "Upload ID not found on server.",
              };
            }
            const castedStatusDetail = statusDetail as ProcessingStatusDetail;

            if (castedStatusDetail.upload_status === "completed") {
              return {
                ...fs,
                uiStatus: "completed_success",
                serverDocumentId: castedStatusDetail.document_id,
              };
            } else if (castedStatusDetail.upload_status === "processing") {
              return { ...fs, uiStatus: "processing_on_server" };
            } else if (castedStatusDetail.upload_status === "error") {
              return {
                ...fs,
                uiStatus: "failed_processing",
                errorMessage: castedStatusDetail.upload_error,
              };
            } else if (castedStatusDetail.upload_status === "queued") {
              return { ...fs, uiStatus: "awaits_processing" }; // Still queued
            }
          }
          return fs; // No change if status not found for some reason
        }),
      );
      checkIfAllDone(); // Check after each poll response
    } catch (error) {
      console.error("Polling failed:", error);
      toast({
        title: "Status Check Failed",
        description: "Could not retrieve processing status for some files.",
        variant: "destructive",
      });
      // Optionally, mark polled files as errored or stop polling
      // For now, it will retry on the next interval. If API is down, polling will keep failing.
    }
  };

  const startPolling = () => {
    if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current); // Clear existing
    setIsPollingActive(true);
    pollUploadStatus(); // Poll immediately
    pollingIntervalRef.current = setInterval(pollUploadStatus, 5000); // Poll every 5 seconds
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPollingActive(false);
  };

  const checkIfAllDone = () => {
    const stillProcessing = files.some(
      (f) =>
        f.uiStatus === "awaits_processing" ||
        f.uiStatus === "processing_on_server" ||
        f.uiStatus === "uploading_to_server",
    );
    if (!stillProcessing && files.length > 0) {
      // Ensure there were files to process
      stopPolling();
      if (onComplete) {
        const allSuccessfullyCompletedOrExisted = files.every(
          (f) =>
            f.uiStatus === "completed_success" ||
            f.uiStatus === "completed_exists",
        );
        if (allSuccessfullyCompletedOrExisted) {
          toast({
            title: "Processing Complete",
            description: "All files have been processed.",
          });
        } else {
          toast({
            title: "Processing Finished",
            description: "Some files could not be processed. Check statuses.",
            variant: "default", // Use default, as individual errors are shown
          });
        }
        onComplete();
      }
    }
  };

  useEffect(() => {
    // Cleanup polling on unmount
    return () => {
      stopPolling();
    };
  }, []);

  // Determine overall progress/status for UI indication
  const getOverallStatus = () => {
    if (files.length === 0) return "idle";
    if (isUploading) return "uploading";
    if (
      files.some(
        (f) =>
          f.uiStatus === "awaits_processing" ||
          f.uiStatus === "processing_on_server",
      )
    )
      return "processing";
    if (
      files.every(
        (f) =>
          f.uiStatus === "completed_success" ||
          f.uiStatus === "completed_exists" ||
          f.uiStatus === "failed_processing" ||
          f.uiStatus === "failed_upload",
      )
    )
      return "done";
    return "pending_selection";
  };

  const overallStatus = getOverallStatus();

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Simplified Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 p-4 bg-muted rounded-lg">
          {overallStatus === "idle" || overallStatus === "pending_selection" ? (
            <FiUpload className="w-10 h-10 text-primary" />
          ) : overallStatus === "uploading" ? (
            <FiLoader className="w-10 h-10 text-primary animate-spin" />
          ) : overallStatus === "processing" ? (
            <FiClock className="w-10 h-10 text-primary animate-pulse" />
          ) : (
            <FiCheckCircle className="w-10 h-10 text-green-500" />
          )}
          <div>
            <h3 className="text-lg font-semibold">
              {overallStatus === "idle" || overallStatus === "pending_selection"
                ? "Select and Upload Files"
                : overallStatus === "uploading"
                  ? "Uploading Files..."
                  : overallStatus === "processing"
                    ? "Processing Files..."
                    : "Processing Complete"}
            </h3>
            <p className="text-sm text-muted-foreground">
              {overallStatus === "idle" || overallStatus === "pending_selection"
                ? "Drag & drop or browse to select documents."
                : overallStatus === "uploading"
                  ? "Sending files to the server."
                  : overallStatus === "processing"
                    ? "Server is processing your documents. This may take a moment."
                    : "All selected files have been processed or encountered an issue."}
            </p>
          </div>
        </div>
      </div>

      <Card className="p-6">
        <div className="space-y-4">
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
              isDragActive
                ? "border-primary bg-primary/5"
                : "hover:border-primary/50",
              (isUploading || isPollingActive) &&
                "cursor-not-allowed opacity-70", // Disable dropzone while uploads/polling are active
            )}
          >
            <input
              {...getInputProps()}
              disabled={isUploading || isPollingActive}
            />
            <FiUpload className="w-12 h-12 mx-auto text-muted-foreground" />
            <p className="mt-2 text-sm font-medium">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Supports PDF, DOCX, DOC, TXT, MD, XLS, XLSX
            </p>
          </div>

          {files.length > 0 && (
            <div className="space-y-2 max-h-[300px] overflow-y-auto border rounded-md p-2">
              {files.map((fs) => (
                <div
                  key={fs.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-background shadow-sm"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 flex-shrink-0">
                      <FileIcon
                        extension={fs.file.name.split(".").pop()?.toLowerCase()}
                        {...defaultStyles[
                          fs.file.name
                            .split(".")
                            .pop()
                            ?.toLowerCase() as keyof typeof defaultStyles
                        ]}
                      />
                    </div>
                    <div className="min-w-0">
                      <p
                        className="text-sm font-medium truncate"
                        title={fs.file.name}
                      >
                        {fs.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(fs.file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {fs.uiStatus === "pending_selection" && (
                      <Badge variant="outline">Pending</Badge>
                    )}
                    {fs.uiStatus === "uploading_to_server" && (
                      <>
                        <FiLoader className="h-4 w-4 animate-spin text-primary" />
                        <span className="text-xs text-primary">
                          Uploading... {fs.progress || 0}%
                        </span>
                      </>
                    )}
                    {fs.uiStatus === "awaits_processing" && (
                      <>
                        <FiClock className="h-4 w-4 text-yellow-500" />
                        <span className="text-xs text-yellow-500">Queued</span>
                      </>
                    )}
                    {fs.uiStatus === "processing_on_server" && (
                      <>
                        <FiLoader className="h-4 w-4 animate-spin text-blue-500" />
                        <span className="text-xs text-blue-500">
                          Processing
                        </span>
                      </>
                    )}
                    {fs.uiStatus === "completed_success" && (
                      <>
                        <FiCheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-xs text-green-500">
                          Completed
                        </span>
                      </>
                    )}
                    {fs.uiStatus === "completed_exists" && (
                      <>
                        <FiHelpCircle className="h-4 w-4 text-blue-400" />
                        <span className="text-xs text-blue-400">Exists</span>
                      </>
                    )}
                    {(fs.uiStatus === "failed_upload" ||
                      fs.uiStatus === "failed_processing") && (
                      <>
                        <FiAlertCircle className="h-4 w-4 text-destructive" />
                        <span
                          className="text-xs text-destructive truncate max-w-[100px]"
                          title={fs.errorMessage || "Failed"}
                        >
                          {fs.errorMessage || "Failed"}
                        </span>
                      </>
                    )}
                    <button
                      onClick={() => removeFile(fs.id)}
                      className="p-1 hover:bg-accent rounded-full disabled:opacity-50"
                      disabled={
                        isUploading ||
                        (isPollingActive &&
                          (fs.uiStatus === "awaits_processing" ||
                            fs.uiStatus === "processing_on_server"))
                      }
                      title="Remove file"
                    >
                      <FiX className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={handleUploadAndInitiateProcessing}
            disabled={
              !files.some((f) => f.uiStatus === "pending_selection") ||
              isUploading ||
              isPollingActive
            }
            className="w-full"
          >
            {isUploading || isPollingActive ? (
              <FiLoader className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FiUpload className="mr-2 h-4 w-4" />
            )}
            {isUploading
              ? "Uploading..."
              : isPollingActive
                ? "Processing..."
                : `Upload ${files.filter((f) => f.uiStatus === "pending_selection").length} File(s)`}
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default DocumentUploadSteps