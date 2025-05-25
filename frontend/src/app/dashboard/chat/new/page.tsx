"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/use-toast";
import { FaPlus, FaFolderOpen } from "react-icons/fa"; // Changed icon
import { FiLoader } from "react-icons/fi"; // Added loader icon
import { useProject, Project } from "@/contexts/project-provider"; // Import Project type

// Removed KnowledgeBase interface

export default function NewChatPage() {
  const router = useRouter();
  const {
    projects,
    isLoading: isLoadingProjects,
    fetchProjects,
  } = useProject(); // Use projects from context
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Projects are fetched by ProjectProvider, ensure they are loaded
    if (!isLoadingProjects && projects.length > 0 && !selectedProjectId) {
      // Optionally auto-select the first project
      // setSelectedProjectId(projects[0].id);
    }
  }, [projects, isLoadingProjects, selectedProjectId]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedProjectId) {
      setError("Please select a project.");
      toast({
        title: "Validation Error",
        description: "You must select a project to start a chat.",
        variant: "destructive",
      });
      return;
    }
    if (!title.trim()) {
      setError("Please enter a chat title.");
      toast({
        title: "Validation Error",
        description: "Chat title cannot be empty.",
        variant: "destructive",
      });
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      // API request body as per new documentation
      const data = await api.post("/api/chat/", {
        title,
        project_id: selectedProjectId,
      });

      router.push(`/dashboard/chat/${data.id}`);
    } catch (err) {
      console.error("Failed to create chat:", err);
      const errorMessage =
        err instanceof ApiError
          ? err.message
          : "Failed to create chat session.";
      setError(errorMessage);
      toast({
        title: "Error Creating Chat",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingProjects) {
    return (
      <div className="max-w-2xl mx-auto space-y-8 animate-pulse">
        <div className="h-8 w-3/4 bg-muted rounded"></div>
        <div className="h-6 w-1/2 bg-muted rounded"></div>
        <div className="space-y-4">
          <div className="h-10 bg-muted rounded"></div>
          <div className="h-20 bg-muted rounded"></div>
          <div className="h-10 w-1/4 bg-muted rounded ml-auto"></div>
        </div>
      </div>
    );
  }

  if (!isLoadingProjects && projects.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <FaFolderOpen className="mx-auto h-16 w-16 text-muted-foreground/50 mb-6" />
        <h2 className="text-3xl font-bold tracking-tight mb-4">
          No Projects Found
        </h2>
        <p className="text-muted-foreground mb-8">
          You need to create at least one project before starting a chat.
          Projects provide the knowledge base for the AI.
        </p>
        <Link
          href="/dashboard/project/new" // Link to create a new project
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          <FaPlus className="mr-2 h-4 w-4" />
          Create Project
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Start New Chat</h2>
        <p className="text-muted-foreground">
          Select a project to provide context for your conversation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label
            htmlFor="title"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Chat Title
          </label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            type="text"
            required
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="E.g., Questions about marketing report"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            Select Project
          </label>
          {/* <div className="text-xs text-muted-foreground">
            The AI will use documents from this project to answer your questions.
          </div> */}
          <div className="grid gap-4 md:grid-cols-1">
            {" "}
            {/* Changed to 1 column for better display of project descriptions */}
            {projects.map(
              (
                project: Project // Explicitly type project
              ) => (
                <label
                  key={project.id}
                  className={`group flex items-center space-x-3 rounded-lg border p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
                    selectedProjectId === project.id
                      ? "border-primary bg-primary/5 shadow-sm ring-2 ring-primary"
                      : "hover:border-primary/30"
                  }`}
                >
                  <input
                    type="radio"
                    name="project-selection" // Changed name for radio group
                    className="peer h-4 w-4 shrink-0 rounded-full border-primary text-primary focus:ring-primary focus:ring-offset-0"
                    checked={selectedProjectId === project.id}
                    onChange={() => setSelectedProjectId(project.id)}
                  />
                  <div className="flex-1 space-y-1">
                    <p className="font-medium group-hover:text-primary transition-colors">
                      {project.project_name}
                    </p>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {project.description || "No description provided."}
                    </p>
                  </div>
                </label>
              )
            )}
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-500 p-3 bg-red-50 rounded-md">
            {error}
          </div>
        )}

        <div className="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={() => router.back()}
            disabled={isSubmitting}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !selectedProjectId || !title.trim()}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            {isSubmitting ? (
              <>
                <FiLoader className="mr-2 h-4 w-4 animate-spin" /> Creating...
              </>
            ) : (
              "Start Chat"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
