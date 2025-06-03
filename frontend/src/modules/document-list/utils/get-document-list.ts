"use server";

import { api } from "@/lib/api-server";

export const getDocumentList = async (projectId: number) => {
  try {
    const data = await api.get(
      `/api/document/project/${projectId}/with-status`
    );
    return data;
  } catch (error) {
    throw new Error(
      `Failed to fetch documents: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
  }
};
