import { api } from "@/lib/api-server";

export const getProjects = async () => {
  try {
    const data = await api.get(`/api/project/user/me`);
    return data;
  } catch (error) {
    return [];
  }
};
