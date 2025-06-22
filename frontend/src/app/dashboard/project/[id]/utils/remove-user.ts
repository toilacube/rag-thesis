"use server";

import { api } from "@/lib/api-server";

export const removeUserFromProject = async (
  projectId: number | string,
  userId: number
) => {
  try {
    const response = await api.delete(
      `/api/users/project/${projectId}/user/${userId}`
    );

    if (response?.status === "success") {
      return {
        success: true,
        message: response.message,
      };
    }

    return {
      success: false,
      message: response?.message || "Unexpected response",
    };
  } catch (error: any) {
    console.error("Error removing user:", error);
    return {
      success: false,
      message: error?.message || "Request failed",
    };
  }
};
