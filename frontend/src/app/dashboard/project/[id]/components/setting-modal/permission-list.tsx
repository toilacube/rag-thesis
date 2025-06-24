import { userPermissions } from "./constant";

interface Props {
  selectedUsers: UserResponse[];
  handleRemoveConfirmation: (user: UserResponse | null) => void;
  handlePermissionChange: (
    userId: number,
    role: string,
    checked: boolean
  ) => void;
}

const PermisstionList = ({
  selectedUsers,
  handleRemoveConfirmation,
  handlePermissionChange,
}: Props) => {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-2">
      {selectedUsers.map((user) => (
        <div
          key={user.id}
          className="border rounded px-3 py-2 bg-gray-50 shadow-sm flex flex-col gap-2 mb-2"
        >
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">{user.email}</span>
            <button
              onClick={() => handleRemoveConfirmation(user)}
              className="text-red-500 hover:text-red-700 text-lg leading-none"
            >
              &times;
            </button>
          </div>

          {/* Roles */}
          <div className="flex flex-wrap gap-3">
            {userPermissions.map((role) => {
              const isAdminSelected = (user.roles || []).includes("admin");
              const isOtherRoleSelected = (user.roles || []).some(
                (r) => r !== "admin"
              );
              const isAutoAssigned =
                user.autoAssignedRoles?.includes(role) ?? false;

              const isDisabled =
                isAutoAssigned ||
                (role === "admin" && isOtherRoleSelected) ||
                (role !== "admin" && isAdminSelected);

              return (
                <label key={role} className="flex items-center gap-1 text-sm">
                  <input
                    type="checkbox"
                    disabled={isDisabled}
                    onChange={(e) =>
                      handlePermissionChange(user.id, role, e.target.checked)
                    }
                    checked={(user.roles || []).includes(role)}
                  />
                  {role}
                </label>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PermisstionList;
