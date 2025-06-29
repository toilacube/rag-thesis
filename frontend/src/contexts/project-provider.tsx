"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

interface Project {
  id: number;
  user_id: number;
  project_name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  documents_count?: number;
  permission_ids?: number[];
}

interface Permission {
  id: number;
  name: string;
  description?: string;
  is_system_level: boolean;
  created_at: string;
  updated_at: string;
}

interface ProjectContextType {
  projects: Project[];
  selectedProject: Project | null;
  permissions: Permission[];
  permissionMap: Record<number, string>; // 👈 Dùng Record thay vì Map
  userId: number | null;
  setSelectedProject: (project: Project | null) => void;
  setProjects: (projects: Project[]) => void;
  setPermissions: (permissions: Permission[]) => void;
  setUserId: (id: number | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider = ({
  children,
  initialProjects = [],
  initialPermissions = [],
  initialSelectedProject = null,
}: {
  children: ReactNode;
  initialProjects?: Project[];
  initialPermissions?: Permission[];
  initialSelectedProject?: Project | null;
}) => {
  const [projects, setProjects] = useState<Project[]>(initialProjects);
  const [permissions, setPermissions] =
    useState<Permission[]>(initialPermissions);
  const [selectedProject, setSelectedProject] = useState<Project | null>(
    initialSelectedProject || initialProjects[0] || null
  );
  const [userId, setUserId] = useState<number | null>(
    initialProjects[0]?.user_id || null
  );
  const [permissionMap, setPermissionMap] = useState<Record<number, string>>(
    {}
  );

  useEffect(() => {
    const map: Record<number, string> = {};
    permissions.forEach((p) => {
      map[p.id] = p.name;
    });
    setPermissionMap(map);
  }, [permissions]);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        setProjects,
        permissions,
        setPermissions,
        permissionMap,
        selectedProject,
        setSelectedProject,
        userId,
        setUserId,
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
