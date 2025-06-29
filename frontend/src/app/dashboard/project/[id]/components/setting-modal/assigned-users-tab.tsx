"use client";

import RemoveConfirmation from "@/components/ui/remove-confirmation";
import { Dispatch, SetStateAction, useEffect } from "react";
import { getAssignedUsers } from "../../utils/get-assigned-users";
import PermisstionList from "./permission-list";

interface AssignedUsersTabProps {
  selectedProjectID?: number;
  id: number | null;
  setId: Dispatch<SetStateAction<number | null>>;
  handleRemove: (userId: number) => Promise<void>;
  handlePermissionChange: (
    userId: number,
    role: string,
    checked: boolean
  ) => void;
  assignedUsers: UserResponse[];
  setAssignedUsers: React.Dispatch<React.SetStateAction<UserResponse[]>>;
}

const AssignedUsersTab = ({
  selectedProjectID,
  id,
  setId,
  handleRemove,
  handlePermissionChange,
  assignedUsers,
  setAssignedUsers,
}: AssignedUsersTabProps) => {
  useEffect(() => {
    const fetchAssignedUsers = async () => {
      if (!selectedProjectID) return;
      try {
        const data = await getAssignedUsers(selectedProjectID);
        const mapped = data.map((user: AssignedUserResponse) => ({
          id: user.user_id,
          email: user.email,
          username: user.username,
          roles: [...(user.permissions || [])],
        }));
        setAssignedUsers(mapped);
      } catch (error) {
        console.error("Error loading assigned users", error);
      }
    };

    fetchAssignedUsers();
  }, [selectedProjectID]);

  const handleRemoveConfirmation = (user: UserResponse | null) => {
    if (!user) return;
    setId(user.id);
  };

  return (
    <>
      <PermisstionList
        selectedUsers={assignedUsers}
        handleRemoveConfirmation={handleRemoveConfirmation}
        handlePermissionChange={handlePermissionChange}
      />

      {id && (
        <RemoveConfirmation id={id} setId={setId} handleRemove={handleRemove} />
      )}
    </>
  );
};
export default AssignedUsersTab;
