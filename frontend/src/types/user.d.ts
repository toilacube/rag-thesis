type User = {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string; // ISO timestamp
  updated_at: string; // ISO timestamp
};

type UserResponse = {
  id: number;
  email: string;
  username: string;
  roles?: string[];
  autoAssignedRoles?: string[];
  trueSelected?: string[];
};

type AssignedUserResponse = {
  user_id: number;
  email: string;
  username: string;
  project_id: number;
  permissions: string[];
};
