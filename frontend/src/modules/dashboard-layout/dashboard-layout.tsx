import Breadcrumb from "@/components/breadcrumb";
import { ProjectProvider } from "@/contexts/project-provider";
import Menu from "./menu";
import { getProjects } from "@/utils/get-projects"; // Import getProjects
import { getPermissions } from "@/utils/get-permissions";

const DashboardLayout = async ({ children }: { children: React.ReactNode }) => {
  const projects: Project[] = await getProjects();
  const permissions: Permission[] = await getPermissions();

  return (
    <ProjectProvider
      initialProjects={projects}
      initialPermissions={permissions}
    >
      <div className="min-h-screen bg-background">
        <Menu />
        <div className="lg:pl-64">
          <main className="min-h-screen py-6 px-4 sm:px-6 lg:px-8">
            <Breadcrumb />
            {children}
          </main>
        </div>
      </div>
    </ProjectProvider>
  );
};

export default DashboardLayout;
