export const checkPermissionName = (
  idList: number[],
  name: string | string[],
  permissionMap: Record<number, string>
): boolean => {
  const permissionNames = Array.isArray(name)
    ? [...name, "admin"]
    : [name, "admin"];

  return idList.some((id) => permissionNames.includes(permissionMap[id]));
};
