"use server";

import { api } from "@/lib/api-server";

export const getAssignedUsers = async (projectId: string | number) => {
  try {
    const response = await api.get(`/api/users/project/${projectId}/users`);
    return response;
  } catch (error) {
    console.error("Failed to get assigned users:", error);
    throw error;
  }
};
