"use client";

import { useEffect, useState } from "react";
import { FiSearch } from "react-icons/fi";
import { useProject } from "@/contexts/project-provider";
import { getUnassignedUsers } from "../../utils/get-unassigned-users";
import { getAssignedUsers } from "../../utils/get-assigned-users";
import { assignUsers } from "../../utils/assign-users";
import { useToast } from "@/components/use-toast";
import { removeUserFromProject } from "../../utils/remove-user";
import {
  computeAutoAssignedMap,
  removeSelectionAndUpdate,
  resolveFullPermissions,
} from "../../utils/permission-dependencies";
import RemoveConfirmation from "./remove-confirmation";
import PermisstionList from "./permission-list";

export default function UserAssignment() {
  const { selectedProject } = useProject();
  const { toast } = useToast();

  const [inputValue, setInputValue] = useState("");
  const [debouncedValue, setDebouncedValue] = useState("");
  const [options, setOptions] = useState<UserResponse[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<UserResponse[]>([]);
  const [confirmUser, setConfirmUser] = useState<UserResponse | null>(null);

  useEffect(() => {
    const fetchAssignedUsers = async () => {
      if (!selectedProject?.id) return;
      try {
        const data = await getAssignedUsers(selectedProject.id);
        const mapped = data.map((user: AssignedUserResponse) => ({
          id: user.user_id,
          email: user.email,
          username: user.username,
          roles: [...(user.permissions || [])],
        }));
        console.log("fetchAssignedUsers", mapped);
        setSelectedUsers(mapped);
      } catch (error) {
        console.error("Error loading assigned users", error);
      }
    };

    fetchAssignedUsers();
  }, [selectedProject?.id]);

  // Debounce logic
  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedValue(inputValue);
    }, 500);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  // Fetch unassigned users
  useEffect(() => {
    if (!debouncedValue || !selectedProject?.id) return;

    const fetchUser = async () => {
      try {
        const result = await getUnassignedUsers(
          selectedProject.id,
          debouncedValue
        );
        const filtered = result.filter(
          (user: UserResponse) => !selectedUsers.some((u) => u.id === user.id)
        );
        setOptions(filtered);
      } catch (err) {
        console.error(err);
      }
    };

    fetchUser();
  }, [debouncedValue, selectedProject?.id, selectedUsers]);

  const handleSelect = (user: UserResponse) => {
    const newUser: UserResponse = {
      ...user,
      roles: ["admin"],
      trueSelected: ["admin"],
      autoAssignedRoles: [],
      isNew: true,
    };

    setSelectedUsers((prev) => [...prev, newUser]);
    setInputValue("");
    setDebouncedValue("");
    setOptions([]);
  };

  const handlePermissionChange = (
    userId: number,
    role: string,
    checked: boolean
  ) => {
    setSelectedUsers((prev) =>
      prev.map((u) => {
        if (u.id !== userId) return u;

        let trueSelected = u.trueSelected || [];
        let updatedRoles: string[] = [];
        let autoAssignedRoles: string[] = [];

        if (checked) {
          let newTrue =
            role === "admin"
              ? ["admin"]
              : [...trueSelected.filter((r) => r !== "admin"), role];
          newTrue = Array.from(new Set(newTrue));
          const autoMap = computeAutoAssignedMap(newTrue);

          trueSelected = newTrue;
          updatedRoles = resolveFullPermissions(trueSelected);
          autoAssignedRoles = Object.keys(autoMap);
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
          ...u,
          roles: updatedRoles,
          autoAssignedRoles,
          trueSelected,
        };
      })
    );
  };

  const handleRemoveConfirmation = (user: UserResponse | null) => {
    if (!user) return;
    if (user?.isNew) {
      setSelectedUsers((prev) => prev.filter((u) => u.id !== user?.id));
      return;
    }
    setConfirmUser(user);
  };

  const handleRemove = async (userId: number) => {
    const user = selectedUsers.find((u) => u.id === userId);
    if (!user || !selectedProject?.id) return;

    const result = await removeUserFromProject(selectedProject.id, userId);

    if (result.success) {
      setSelectedUsers((prev) => prev.filter((u) => u.id !== userId));
      toast({ title: "Removed!", description: result.message });
    } else {
      toast({
        title: "Error",
        description: result.message,
        variant: "destructive",
      });
    }
  };

  const handleAssign = async () => {
    if (!selectedProject?.id) {
      alert("Missing project ID");
      return;
    }
    console.log("selectedUsers", selectedUsers);

    try {
      await assignUsers(selectedProject.id, selectedUsers);
      toast({
        title: "Assigned!",
        description: "Users assigned successfully!",
      });
      setSelectedUsers((prev) =>
        prev.map((user) => ({
          ...user,
          isNew: false,
        }))
      );
    } catch (error) {
      console.error(error);
      toast({
        title: "Failed",
        description: "Failed to assign users.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="relative w-full max-w-md h-[400px] bg-white flex flex-col">
      {/* Sticky Header */}
      <div className="sticky top-0 bg-white z-10 px-4 py-2 border-b">
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
          />
        </div>

        {/* Dropdown options */}
        {options.length > 0 && (
          <ul className="absolute z-20 w-full bg-white shadow-md border rounded mt-1 max-h-60 overflow-y-auto">
            {options.map((user) => (
              <li
                key={user.id}
                onClick={() => handleSelect(user)}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
              >
                {user.email}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Scrollable content */}
      <PermisstionList
        selectedUsers={selectedUsers}
        handleRemoveConfirmation={handleRemoveConfirmation}
        handlePermissionChange={handlePermissionChange}
      />

      {/* Sticky Footer with Submit Button */}
      <div className="bg-white z-10 px-4 py-2 border-t">
        <button
          className="w-full bg-gray-800 text-white py-2 rounded hover:bg-gray-700 transition"
          onClick={handleAssign}
        >
          Assign Users
        </button>
      </div>
      {confirmUser && (
        <RemoveConfirmation
          confirmUser={confirmUser}
          setConfirmUser={setConfirmUser}
          handleRemove={handleRemove}
        />
      )}
    </div>
  );
}
