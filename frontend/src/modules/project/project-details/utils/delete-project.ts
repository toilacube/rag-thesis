"use server";

import { api } from "@/lib/api-server";

export const deleteProject = async (id: number) => {
    try {
        const response = await api.delete(`/api/project/${id}`);
        return response;
    } catch (error) {
        console.error("Failed to delete project:", error);
        throw error;
    }
};