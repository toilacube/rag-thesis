"use server";

import { api } from "@/lib/api-server";

export const assignUsers = async (
  projectId: string | number,
  selectedUsers: UserResponse[]
): Promise<AssignedUserResponse[]> => {
  try {
    const response = await api.post(
      `/api/users/project/${projectId}/users-batch-assignment`,
      {
        users: selectedUsers.map((user) => ({
          email: user.email,
          permissions: user.roles || [],
        })),
      }
    );
    return response;
  } catch (error) {
    console.error("Failed to get chat list:", error);
    throw error;
  }
};
