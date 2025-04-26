"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileIcon, defaultStyles } from "react-file-icon";
import {
  FiArrowRight,
  FiPlus,
  FiSettings,
  FiTrash2,
  FiSearch,
} from "react-icons/fi";
import { useProject } from "@/contexts/ProjectContext";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/use-toast";

interface Document {
  id: number;
  file_name: string;
  file_path: string;
  file_size: number;
  content_type: string;
  knowledge_base_id: number;
  created_at: string;
  updated_at: string;
  processing_tasks: any[];
}

export default function ProjectsPage() {
  const {
    projects,
    fetchProjects,
    isLoading,
    selectedProject,
    setSelectedProject,
  } = useProject();
  const { toast } = useToast();

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this project?")) return;

    try {
      const response = await api.delete(`/api/project/${id}`);
      toast({
        title: "Success",
        description: `Project deleted successfully (ID: ${response.project_id})`,
      });
      fetchProjects();
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
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">
            Manage your projects and documents
          </p>
        </div>
        <Link
          href="/dashboard/project/new"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <FiPlus className="mr-2 h-4 w-4" />
          New Project
        </Link>
      </div>

      <div className="grid gap-6">
        {projects.map((project) => (
          <div
            key={project.id}
            className={`rounded-lg border bg-card p-6 space-y-4 ${
              selectedProject?.id === project.id ? "ring-2 ring-primary" : ""
            }`}
            onClick={() => setSelectedProject(project)}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{project.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {project.description || "No description"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {project.documents_count || 0} documents •{" "}
                  {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>

              <div className="flex space-x-2">
                <Link
                  href={`/dashboard/project/${project.id}`}
                  className="inline-flex items-center justify-center rounded-md bg-secondary w-8 h-8"
                >
                  <FiSettings className="h-4 w-4" />
                </Link>
                <Link
                  href={`/dashboard/test-retrieval/${project.id}`}
                  className="inline-flex items-center justify-center rounded-md bg-secondary w-8 h-8"
                >
                  <FiSearch className="h-4 w-4" />
                </Link>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(project.id);
                  }}
                  className="inline-flex items-center justify-center rounded-md bg-destructive/10 hover:bg-destructive/20 w-8 h-8"
                >
                  <FiTrash2 className="h-4 w-4 text-destructive" />
                </button>
              </div>
            </div>

            {(project.documents_count ?? 0) > 0 && (
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-2">Documents</h4>
                <Link
                  href={`/dashboard/project/${project.id}`}
                  className="inline-flex items-center text-sm text-primary hover:underline"
                >
                  View all documents
                  <FiArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </div>
            )}
          </div>
        ))}

        {!isLoading && projects.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              No projects found. Create one to get started.
            </p>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="space-y-4">
              <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto"></div>
              <p className="text-muted-foreground animate-pulse">
                Loading projects...
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
