"use server";

import { api } from "@/lib/api-server";

export const checkLoggedIn = async (): Promise<boolean> => {
  try {
    const data = await api.get("/api/auth/me");
    return data.is_active;
  } catch (error) {
    return false;
  }
};
