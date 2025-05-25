import DashboardClient from "./dashboard.client";
import { ProjectProvider } from "@/contexts/project-provider";
import { getProjects } from "@/utils/get-projects";

const Dashboard = async () => {
    const projects = await getProjects();

    return (
        <ProjectProvider initialProjects={projects}>
            <DashboardClient />
        </ProjectProvider>
    );
};

export default Dashboard;
