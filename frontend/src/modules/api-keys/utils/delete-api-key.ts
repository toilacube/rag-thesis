"use server";

import { api } from "@/lib/api-server";

export const deleteAPIKey = async (id: number) => {
  try {
    const response = await api.delete(`/api/api-keys/${id}`);

    if (!response.ok) throw new Error("Failed to delete API key");

    return response;
  } catch (error) {
    return error;
  }
};
