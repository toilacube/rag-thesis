"use client";

import { useState } from "react";
import { userPermissions } from "./constant";
import { Pencil, Check } from "lucide-react";

interface Props {
  selectedUsers: UserResponse[];
  handleRemoveConfirmation: (user: UserResponse) => void;
  handlePermissionChange: (
    userId: number,
    role: string,
    checked: boolean
  ) => void;
  handleSaveUser?: (user: UserResponse) => Promise<void>;
  enableEditMode?: boolean;
}

const PermisstionList = ({
  selectedUsers,
  handleRemoveConfirmation,
  handlePermissionChange,
  handleSaveUser,
  enableEditMode = false,
}: Props) => {
  const [editingUserIds, setEditingUserIds] = useState<number[]>([]);

  const handleRemove = (user: UserResponse | null, isEditing: boolean) => {
    if (!user) return;

    if (isEditing) {
      setEditingUserIds((prev) => prev.filter((id) => id !== user.id));
    } else {
      handleRemoveConfirmation(user);
    }
  };

  const toggleEdit = (userId: number) => {
    setEditingUserIds((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-2">
      {selectedUsers.map((user) => {
        const isEditing = editingUserIds.includes(user.id);

        return (
          <div
            key={user.id}
            className="border rounded px-3 py-2 bg-gray-50 shadow-sm flex flex-col gap-2 mb-2"
          >
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">{user.email}</span>

              <div className="flex items-center gap-2">
                {enableEditMode && (
                  <>
                    {isEditing ? (
                      <button
                        onClick={async () => {
                          if (handleSaveUser) {
                            await handleSaveUser(user);
                          }
                          setEditingUserIds((prev) =>
                            prev.filter((id) => id !== user.id)
                          );
                        }}
                        className={`text-${
                          user.roles?.length ? "green" : "gray"
                        }-600 hover:text-${
                          user.roles?.length ? "green" : "gray"
                        }-800`}
                        title="Save Changes"
                        disabled={!user.roles?.length}
                      >
                        <Check size={13} />
                      </button>
                    ) : (
                      <button
                        onClick={() => toggleEdit(user.id)}
                        className="text-blue-500 hover:text-blue-700"
                        title="Edit Permissions"
                      >
                        <Pencil size={13} />
                      </button>
                    )}
                  </>
                )}
                <button
                  onClick={() => handleRemove(user, isEditing)}
                  className={`text-${
                    isEditing ? "gray" : "red"
                  }-500 hover:text-${
                    isEditing ? "gray" : "red"
                  }-700 text-lg leading-none`}
                >
                  &times;
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              {userPermissions.map((role) => {
                const isAdminSelected = (user.roles || []).includes("admin");
                const isOtherRoleSelected = (user.roles || []).some(
                  (r) => r !== "admin"
                );
                const isAutoAssigned =
                  user.autoAssignedRoles?.includes(role) ?? false;

                const isDisabled =
                  !isEditing && enableEditMode
                    ? true
                    : isAutoAssigned ||
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
        );
      })}
    </div>
  );
};

export default PermisstionList;
