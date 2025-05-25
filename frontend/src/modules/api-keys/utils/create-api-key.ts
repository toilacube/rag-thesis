"use server";

import { api } from "@/lib/api-server";

export const createAPIKey = async (name: string) => {
  try {
    const data = await api.post("/api/api-keys", {
      name,
      is_active: true,
    });

    if (!data.ok) throw new Error("Failed to create API key");

    return data;
  } catch (error) {
    return error;
  }
};
