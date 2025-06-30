"use client";

import RemoveConfirmation from "@/components/ui/remove-confirmation";
import { Dispatch, SetStateAction, useEffect } from "react";
import { getAssignedUsers } from "../../utils/get-assigned-users";
import PermisstionList from "./permission-list";
import {
  computeAutoAssignedMap,
  removeSelectionAndUpdate,
  resolveFullPermissions,
} from "../../utils/permission-dependencies";
import { editUserPermission } from "../../utils/edit-user-permission";

interface AssignedUsersTabProps {
  selectedProjectID?: number;
  id: number | null;
  setId: Dispatch<SetStateAction<number | null>>;
  handleRemove: (userId: number) => Promise<void>;
  assignedUsers: UserResponse[];
  setAssignedUsers: React.Dispatch<React.SetStateAction<UserResponse[]>>;
}

const AssignedUsersTab = ({
  selectedProjectID,
  id,
  setId,
  handleRemove,
  assignedUsers,
  setAssignedUsers,
}: AssignedUsersTabProps) => {
  useEffect(() => {
    console.log("assignedUsers", assignedUsers);
    const fetchAssignedUsers = async () => {
      if (!selectedProjectID) return;
      try {
        const data = await getAssignedUsers(selectedProjectID);
        const mapped = data.map((user: AssignedUserResponse) => {
          const trueSelected = [...(user.permissions || [])];
          const autoMap = computeAutoAssignedMap(trueSelected);
          return {
            id: user.user_id,
            email: user.email,
            username: user.username,
            trueSelected,
            roles: resolveFullPermissions(trueSelected),
            autoAssignedRoles: Object.keys(autoMap),
          };
        });

        setAssignedUsers(mapped);
      } catch (error) {
        console.error("Error loading assigned users", error);
      }
    };

    fetchAssignedUsers();
  }, [selectedProjectID]);

  const handleRemoveConfirmation = (user: UserResponse) => {
    setId(user.id);
  };

  const handlePermissionChange = (
    userId: number,
    role: string,
    checked: boolean
  ) => {
    setAssignedUsers((prev) =>
      prev.map((user) => {
        if (user.id !== userId) return user;

        let trueSelected = user.trueSelected || [];
        let updatedRoles: string[] = [];
        let autoAssignedRoles: string[] = [];

        if (checked) {
          let newTrue =
            role === "admin"
              ? ["admin"]
              : [...trueSelected.filter((r) => r !== "admin"), role];
          newTrue = Array.from(new Set(newTrue));

          const autoMap = computeAutoAssignedMap(newTrue);
          updatedRoles = resolveFullPermissions(newTrue);
          autoAssignedRoles = Object.keys(autoMap);
          trueSelected = newTrue;
        } else {
          const {
            updatedSelected,
            autoAssignedMap,
            trueSelected: newTrue,
          } = removeSelectionAndUpdate(role, trueSelected);

          updatedRoles = updatedSelected;
          autoAssignedRoles = Object.keys(autoAssignedMap);
          trueSelected = newTrue;
        }

        return {
          ...user,
          roles: updatedRoles,
          autoAssignedRoles,
          trueSelected,
        };
      })
    );
  };

  const handleSaveUser = async (user: UserResponse) => {
    if (!selectedProjectID || !user.id || !user.roles?.length) return;
    try {
      await editUserPermission(selectedProjectID, user.id, user.roles);
    } catch (error) {
      console.error("Error saving user permission", error);
    }
  };

  return (
    <>
      <PermisstionList
        selectedUsers={assignedUsers}
        handleRemoveConfirmation={handleRemoveConfirmation}
        handlePermissionChange={handlePermissionChange}
        enableEditMode={true}
        handleSaveUser={handleSaveUser}
      />

      {id && (
        <RemoveConfirmation id={id} setId={setId} handleRemove={handleRemove} />
      )}
    </>
  );
};
export default AssignedUsersTab;
