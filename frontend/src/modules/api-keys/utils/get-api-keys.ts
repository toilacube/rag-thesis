"use server";

import { api } from "@/lib/api-server";

export const getAPIKeys = async () => {
  try {
    const data = await api.get("/api/api-keys");
    return data;
  } catch (error) {
    return [];
  }
};
