import { checkLoggedIn } from "@/utils/check-logged-in";
import DashboardClient from "./dashboard.client";
import { redirect } from "next/navigation";

const Dashboard = async () => {
  const isLoggedIn = await checkLoggedIn();
  if (!isLoggedIn) {
    redirect("/login");
  }
  return <DashboardClient />;
};

export default Dashboard;
