"use client";
import { useState, useEffect } from "react";
import { useProject } from "@/contexts/project-provider";
import { useToast } from "@/components/use-toast";
import { getUnassignedUsers } from "../../utils/get-unassigned-users";
import { assignUsers } from "../../utils/assign-users";
import { removeUserFromProject } from "../../utils/remove-user";
import {
  computeAutoAssignedMap,
  removeSelectionAndUpdate,
  resolveFullPermissions,
} from "../../utils/permission-dependencies";
import AddUsersTab from "./add-users-tab";
import AssignedUsersTab from "./assigned-users-tab";

export default function UserAssignment() {
  const { selectedProject } = useProject();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState<"assigned" | "search">("assigned");

  const [inputValue, setInputValue] = useState("");
  const [debouncedValue, setDebouncedValue] = useState("");
  const [options, setOptions] = useState<UserResponse[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<UserResponse[]>([]);
  const [assignedUsers, setAssignedUsers] = useState<UserResponse[]>([]);
  const [id, setId] = useState<number | null>(null);

  // Debounce
  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedValue(inputValue);
    }, 500);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  // Fetch unassigned users
  useEffect(() => {
    if (!debouncedValue || !selectedProject?.id) {
      setOptions([]);
      return;
    }

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
    setSelectedUsers((prev) => prev.filter((u) => u.id !== user?.id));
  };

  const handleRemove = async (userId: number) => {
    const user = assignedUsers.find((u) => u.id === userId);
    if (!user || !selectedProject?.id) return;

    const result = await removeUserFromProject(selectedProject.id, userId);

    if (result.success) {
      setAssignedUsers((prev) => prev.filter((u) => u.id !== userId));
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

    try {
      await assignUsers(selectedProject.id, selectedUsers);
      setAssignedUsers((prev) => [
        ...prev,
        ...selectedUsers.map((user) => ({
          ...user,
          isNew: false,
        })),
      ]);
      setSelectedUsers([]);
      toast({
        title: "Assigned!",
        description: "Users assigned successfully!",
      });
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
    <div className="relative w-full max-w-md h-[500px] bg-white flex flex-col">
      {/* Tab Header */}
      <div className="sticky top-0 bg-white z-10 px-4 border-b">
        <div className="flex">
          <div
            className={`flex-1 py-2 text-center cursor-pointer ${
              activeTab === "assigned"
                ? "border-b-2 border-gray-800 font-semibold"
                : "text-gray-500"
            }`}
            onClick={() => setActiveTab("assigned")}
          >
            Assigned Users
          </div>
          <div
            className={`flex-1 py-2 text-center cursor-pointer ${
              activeTab === "search"
                ? "border-b-2 border-gray-800 font-semibold"
                : "text-gray-500"
            }`}
            onClick={() => setActiveTab("search")}
          >
            Add Users
          </div>
        </div>
      </div>

      {activeTab === "assigned" ? (
        <AssignedUsersTab
          selectedProjectID={selectedProject?.id}
          assignedUsers={assignedUsers}
          setAssignedUsers={setAssignedUsers}
          handlePermissionChange={handlePermissionChange}
          id={id}
          setId={setId}
          handleRemove={handleRemove}
        />
      ) : (
        <AddUsersTab
          inputValue={inputValue}
          setInputValue={setInputValue}
          options={options}
          selectedUsers={selectedUsers}
          handlePermissionChange={handlePermissionChange}
          handleRemoveConfirmation={handleRemoveConfirmation}
          handleAssign={handleAssign}
          handleSelect={handleSelect}
        />
      )}
    </div>
  );
}
