"use client";

import { useParams } from "next/navigation";
import { useState, useCallback } from "react";
import { DocumentList } from "@/modules/knowledge-base/document-list";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/dialog";
import { FiPlus } from "react-icons/fi";
import { Button } from "@/components/button";

export default function KnowledgeBasePage() {
  const params = useParams();
  const knowledgeBaseId = parseInt(params.id as string);
  const [refreshKey, setRefreshKey] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleUploadComplete = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
    setDialogOpen(false);
  }, []);

  return (
    <>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Knowledge Base</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <FiPlus className="w-4 h-4 mr-2" />
              Add Document
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Add Document</DialogTitle>
              <DialogDescription>
                Upload a document to your knowledge base. Supported formats:
                PDF, DOCX, Markdown, and Text files.
              </DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      </div>

      <div className="mt-8">
        <DocumentList key={refreshKey} knowledgeBaseId={knowledgeBaseId} />
      </div>
    </>
  );
}
