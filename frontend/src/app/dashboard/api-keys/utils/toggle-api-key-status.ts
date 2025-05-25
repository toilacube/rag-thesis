"use server";

import { api } from "@/lib/api-server";

export const toggleAPIKeyStatus = async (
  id: number,
  currentStatus: boolean
) => {
  try {
    const response = await api.put(`/api/api-keys/${id}`, {
      is_active: !currentStatus,
    });

    if (!response.ok) throw new Error("Failed to toggle API key");

    return response;
  } catch (error) {
    return error;
  }
};
