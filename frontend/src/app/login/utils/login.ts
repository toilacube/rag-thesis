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
      // console.log("response.access_token", response.access_token); // Optional: keep for debugging if needed
      return { success: true, token: response.access_token };
    }
    // If no access_token, but still a successful login response structure (though unlikely for login)
    // Or handle as an error if token is always expected on success
    return { success: false, message: "Login successful but no token received" };
  } catch (error) {
    // It's good practice to log the actual error on the server for debugging
    console.error("Login action error:", error);
    // Check if error is an object and has a message property
    const errorMessage = (error instanceof Error) ? error.message : "Login failed due to an unexpected error";
    return { success: false, message: errorMessage };
  }
};
