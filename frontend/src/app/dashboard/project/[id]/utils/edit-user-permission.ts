"use server";

import { api } from "@/lib/api-server";

export const editUserPermission = async (
  projectId: number | string,
  userId: number,
  roles: string[]
) => {
  try {
    const response = await api.put(
      `/api/users/project/${projectId}/user/${userId}/permissions`,
      roles
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
    console.error("Error updating permissions:", error);
    return {
      success: false,
      message: error?.message || "Request failed",
    };
  }
};
