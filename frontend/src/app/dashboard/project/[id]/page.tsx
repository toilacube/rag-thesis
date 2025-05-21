"use client";

import { useParams } from "next/navigation";
import { useState, useCallback } from "react";
import { DocumentUploadSteps } from "@/modules/knowledge-base/document-upload-steps"; // Ensure path is correct
import { DocumentList } from "@/modules/knowledge-base/document-list"; // Ensure path is correct
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
import { useProject } from "@/contexts/ProjectContext"; // Import useProject
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"; // For project info display

export default function ProjectDetailPage() { // Renamed for clarity
  const params = useParams();
  const projectId = parseInt(params.id as string);
  const [refreshKey, setRefreshKey] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { projects, isLoading: projectLoading } = useProject(); // Get projects to display name/desc

  const currentProject = projects.find(p => p.id === projectId);

  const handleUploadComplete = useCallback(() => {
    setRefreshKey((prev) => prev + 1); // This will re-render DocumentList which fetches new data
    setDialogOpen(false); // Close the dialog
  }, []);

  if (projectLoading) {
    return <div className="p-8 text-center">Loading project details...</div>;
  }

  if (!currentProject && !projectLoading) {
     return <div className="p-8 text-center text-destructive">Project not found.</div>;
  }

  return (
    <div className="space-y-8">
       {currentProject && (
         <Card>
            <CardHeader>
                <CardTitle className="text-2xl">{currentProject.name}</CardTitle>
                {currentProject.description && <p className="text-muted-foreground">{currentProject.description}</p>}
            </CardHeader>
            {/* You can add more project details here if needed */}
         </Card>
       )}

      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Project Documents</h2>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <FiPlus className="w-4 h-4 mr-2" />
              Add Documents
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl min-h-[60vh] flex flex-col"> {/* Increased min height */}
            <DialogHeader>
              <DialogTitle>Add Documents to Knowledge Base</DialogTitle>
              <DialogDescription>
                Upload documents to "{currentProject?.name || `Project ID ${projectId}`}".
                Supported formats: PDF, DOCX, DOC, TXT, MD, XLS, XLSX.
              </DialogDescription>
            </DialogHeader>
            <div className="flex-grow overflow-y-auto py-4"> {/* Make the steps component scrollable */}
                <DocumentUploadSteps
                projectId={projectId}
                onComplete={handleUploadComplete}
                />
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="mt-2"> {/* Reduced top margin as title is separate now */}
        <DocumentList key={refreshKey} projectId={projectId} />
      </div>
    </div>
  );
}