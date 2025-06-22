"use server";

import { api } from "@/lib/api-server";

export const checkLoggedIn = async (token?: string): Promise<User | null> => {
  try {
    const data = await api.get("/api/auth/me", {
      ...(token && { token }),
    });
    return data;
  } catch (error) {
    console.error(error);
    return null;
  }
};
