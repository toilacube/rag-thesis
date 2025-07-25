"use client";

import { ApiError } from "@/lib/api";
import { useProject } from "@/contexts/project-provider";
import { useToast } from "@/components/use-toast";
import Link from "next/link";
import { FiTrash2, FiArrowRight } from "react-icons/fi";
import { deleteProject } from "./utils/delete-project";
import { useRouter } from "next/navigation";
import { checkPermissionName } from "@/utils/check-permission-name";
import RemoveConfirmation from "@/components/ui/remove-confirmation";
import { useState } from "react";

const ProjectDetails = () => {
  const router = useRouter();
  const {
    projects,
    setProjects,
    selectedProject,
    setSelectedProject,
    permissionMap,
  } = useProject();
  const { toast } = useToast();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  console.log("toilacube:", projects);
  console.log("permissionMap", permissionMap);

  const handleDelete = async (id: number) => {
    try {
      const response = await deleteProject(id);
      toast({
        title: "Success",
        description: `Project deleted successfully (ID: ${response.project_id})`,
      });
      setProjects(projects.filter((project) => project.id !== id));
    } catch (error) {
      console.error("Failed to delete project:", error);
      if (error instanceof ApiError) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
      }
    }
  };

  return (
    <div className="grid gap-6">
      {projects.map((project) => (
        <div
          key={project.id}
          className={`rounded-lg border bg-card p-6 space-y-4 cursor-pointer ${
            selectedProject?.id === project.id ? "ring-2 ring-primary" : ""
          }`}
          onClick={() => {
            setSelectedProject(project);
            router.push(`/dashboard/project/${project.id}`);
          }}
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold">{project.project_name}</h3>
              <p className="text-sm text-muted-foreground">
                {project.description || "No description"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {project.documents_count || 0} documents
              </p>
            </div>

            {!!project?.permission_ids?.length &&
              checkPermissionName(
                project.permission_ids,
                "delete_project",
                permissionMap
              ) && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedId(project.id);
                  }}
                  className="inline-flex items-center justify-center rounded-md bg-destructive/10 hover:bg-destructive/20 w-8 h-8"
                >
                  <FiTrash2 className="h-4 w-4 text-destructive" />
                </button>
              )}
          </div>

          {(project.documents_count ?? 0) > 0 && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-2">Documents</h4>
              <Link
                href={`/dashboard/project`}
                className="inline-flex items-center text-sm text-primary hover:underline"
              >
                View all documents
                <FiArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      ))}

      {projects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No projects found. Create one to get started.
          </p>
        </div>
      )}

      {selectedId && (
        <RemoveConfirmation
          id={selectedId}
          setId={setSelectedId}
          handleRemove={handleDelete}
        />
      )}
    </div>
  );
};

export default ProjectDetails;
