"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/dialog";
import { FiPlus } from "react-icons/fi";
import { Button } from "@/components/ui/button";
import { DocumentUploadSteps } from "@/modules/document-upload-steps";

type UploadModalProps = {
  dialogOpen: boolean;
  setDialogOpen: (open: boolean) => void;
  projectId: number;
  currentProject?: { project_name?: string };
  handleUploadComplete: () => void;
};

const UploadModal = ({
  dialogOpen,
  setDialogOpen,
  projectId,
  currentProject,
  handleUploadComplete,
}: UploadModalProps) => {
  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          <FiPlus className="w-4 h-4 mr-2" />
          Add Documents
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl min-h-[60vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Add Documents to Knowledge Base</DialogTitle>
          <DialogDescription>
            {`Upload documents to "`}
            {currentProject?.project_name || `Project ID ${projectId}`}
            {`". Supported formats: PDF, DOCX, DOC, TXT, MD, XLS, XLSX.`}
          </DialogDescription>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto py-4">
          <DocumentUploadSteps
            projectId={projectId}
            onComplete={handleUploadComplete}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UploadModal;
