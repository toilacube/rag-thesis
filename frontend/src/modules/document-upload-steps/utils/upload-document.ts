"use server";

import { api } from "@/lib/api-server";

export const uploadDocument = async (formData: FormData) => {

  try {
    const response = await api.post(
        `/api/document/upload`,
        formData,
        { headers: {} }, // Content-Type will be set automatically for FormData
      );
    return response;
  } catch (error) {
    throw Error
  }
};
