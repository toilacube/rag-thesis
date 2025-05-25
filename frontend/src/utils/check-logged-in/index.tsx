"use server";

import { api } from "@/lib/api-server";

export const checkLoggedIn = async (token?: string): Promise<boolean> => {
  try {
    const data = await api.get("/api/auth/me", {
      ...(token && { token }),
    });
    return data.is_active;
  } catch (error) {
    return false;
  }
};
