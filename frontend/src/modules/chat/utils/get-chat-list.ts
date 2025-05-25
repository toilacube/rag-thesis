'use server';

import { api } from "@/lib/api-server";

export const getChatList = async () => {
  try {
    const response = await api.get("/api/chat/");
    return response;
  } catch (error) {
    console.error("Failed to get chat list:", error);
    throw error;
  }
};