"use server";

import { api } from "@/lib/api-server";

export const getUnassignedUsers = async (
  projectId: string | number,
  query: string
) => {
  try {
    const response = await api.get(
      `/api/project/${projectId}/unassigned-users?q=${query}`
    );
    return response;
  } catch (error) {
    console.error("Failed to get chat list:", error);
    throw error;
  }
};
