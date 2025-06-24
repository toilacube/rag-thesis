"use client";

import { useParams } from "next/navigation";
import { useState, useCallback } from "react";
import { DocumentList } from "@/modules/document-list";
import { useProject } from "@/contexts/project-provider"; // Import useProject
import { Card, CardHeader, CardTitle } from "@/components/card"; // For project info display
import UploadModal from "./components/upload-modal";
import { SettingModal } from "./components/setting-modal";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = parseInt(params.id as string);
  const [refreshKey, setRefreshKey] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { projects } = useProject(); // Get projects to display name/desc

  const currentProject = projects.find((p) => p.id === projectId);

  const handleUploadComplete = useCallback(() => {
    setRefreshKey((prev) => prev + 1); // This will re-render DocumentList which fetches new data
    setDialogOpen(false); // Close the dialog
  }, []);

  if (!currentProject) {
    return (
      <div className="p-8 text-center text-destructive">Project not found.</div>
    );
  }

  return (
    <div className="space-y-8">
      {currentProject && (
        <Card>
          <CardHeader className="flex flex-row justify-between gap-4">
            <div>
              <CardTitle className="text-2xl">
                {currentProject.project_name}
              </CardTitle>
              {currentProject.description && (
                <p className="text-muted-foreground">
                  {currentProject.description}
                </p>
              )}
            </div>
            <SettingModal />
          </CardHeader>
          {/* You can add more project details here if needed */}
        </Card>
      )}

      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Project Documents</h2>
        <UploadModal
          dialogOpen={dialogOpen}
          setDialogOpen={setDialogOpen}
          projectId={projectId}
          currentProject={currentProject}
          handleUploadComplete={handleUploadComplete}
        />
      </div>

      <div className="mt-2">
        {/* Reduced top margin as title is separate now */}
        <DocumentList key={refreshKey} projectId={projectId} />
      </div>
    </div>
  );
}
