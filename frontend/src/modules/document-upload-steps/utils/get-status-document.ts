"use server";

import { api } from "@/lib/api-server";

export const getStatusDocument = async (queryParams: URLSearchParams) => {
  try {
    const data = await api.get(`/api/document/upload/status?${queryParams.toString()}`);
    return data;
  } catch (error) {
    throw Error
  }
};
