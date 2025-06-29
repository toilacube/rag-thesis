import { api } from "@/lib/api-server";

export const getPermissions = async () => {
  try {
    const data = await api.get(`/api/permissions`);
    return data;
  } catch (error) {
    return [];
  }
};
