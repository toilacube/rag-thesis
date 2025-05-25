"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export interface Project {
  id: number;
  project_name: string;
  description: string;
  created_at: string;
  updated_at?: string;
  documents_count?: number;
}

interface ProjectContextType {
  projects: Project[];
  selectedProject: Project | null;
  setSelectedProject: (project: Project | null) => void;
  setProjects: (projects: Project[]) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider = ({
  children,
  initialProjects = [],
  initialSelectedProject = null,
}: {
  children: ReactNode;
  initialProjects?: Project[];
  initialSelectedProject?: Project | null;
}) => {
  const [projects, setProjects] = useState<Project[]>(initialProjects);
  const [selectedProject, setSelectedProject] = useState<Project | null>(
    initialSelectedProject || initialProjects[0] || null,
  );

  return (
    <ProjectContext.Provider
      value={{
        projects,
        setProjects,
        selectedProject,
        setSelectedProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
};
