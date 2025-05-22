"use server";

import { api } from "@/lib/api-server";
import { cookies } from "next/headers";

export const loginAction = async (formData: FormData) => {
  const email = formData.get("email");
  const password = formData.get("password");

  try {
    const response = await api.post("/api/auth/login", {
      email: email,
      password: password,
    });
    if (response.access_token) {
      const cookieStore = await cookies();
      cookieStore.set("token", response.access_token);
      console.log("response.access_token", response.access_token);
    }

    return { success: true };
  } catch (error) {
    return { success: false, message: "Login failed" };
  }
};
