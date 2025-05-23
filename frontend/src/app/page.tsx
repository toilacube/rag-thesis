import { checkLoggedIn } from "@/utils/check-logged-in";
import { redirect } from "next/navigation";

const Home = async () => {
  const isLoggedIn = await checkLoggedIn();

  if (!isLoggedIn) {
    redirect("/login");
  }

  redirect("/dashboard");
};

export default Home;
