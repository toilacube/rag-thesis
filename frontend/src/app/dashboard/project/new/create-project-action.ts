"use server";

import { api, ApiError } from "@/lib/api-server";

export const createProject = async (formData: FormData) => {
  const name = formData.get("name");
  const description = formData.get("description");

  try {
    const response = await api.post("/api/project", {
      project_name: name,
      description: description || "",
    });
    return { success: true, project: response };
  } catch (error) {
    return {
      success: false,
      message:
        error instanceof ApiError ? error.message : "Failed to create project",
    };
  }
};
