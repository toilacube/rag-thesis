"use server";

import { api } from "@/lib/api-server";
import { ApiError } from "@/lib/api";

export const previewDocumentAction = async (documentId: number) => {
  if (!documentId) {
    return { success: false, message: "Document ID is missing." };
  }
  try {
    const response = await api.get(`/api/document/${documentId}/markdown`);
    // API now returns a JSON object with the markdown content in the 'content' property
    if (response && response.content) {
      return { success: true, markdown: response.content };
    }
    // If the response doesn't have the expected structure
    return { success: false, message: "Invalid response format from API." };
  } catch (error) {
    console.error(
      "Failed to fetch markdown for preview via server action:",
      error
    );
    const errorMessage =
      error instanceof ApiError ? error.message : "Failed to load preview.";
    return { success: false, message: errorMessage };
  }
};
