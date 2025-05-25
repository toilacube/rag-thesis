import { ProjectDetails } from "@/modules/project/project-details";
import Link from "next/link";
import { FiPlus } from "react-icons/fi";

const ProjectsPage = () => {
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
      <ProjectDetails />
    </div>
  );
};

export default ProjectsPage;
