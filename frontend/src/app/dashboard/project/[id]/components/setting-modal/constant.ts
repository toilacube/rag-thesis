export const userPermissions = [
  "admin",
  "view_project",
  "edit_project",
  "delete_project",
  "add_document",
  "edit_document",
  "delete_document",
  "manage_api_keys",
] as const;

export const dependencyMap: Record<string, string[]> = {
  edit_project: [
    "view_project",
    "add_document",
    "edit_document",
    "delete_document",
  ],
  delete_project: ["view_project"],
  add_document: ["view_project", "edit_project"],
  edit_document: ["view_project", "edit_project"],
  delete_document: ["view_project", "edit_project"],
};

export const reverseDependencyMap: Record<string, string[]> = {
  edit_project: ["add_document", "edit_document", "delete_document"],
  view_project: [
    "edit_project",
    "add_document",
    "edit_document",
    "delete_document",
    "manage_api_keys",
  ],
  delete_project: [],
  add_document: [],
  edit_document: [],
  delete_document: [],
};
