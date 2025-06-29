"use client";

import { FiSearch } from "react-icons/fi";
import PermisstionList from "./permission-list";

interface Props {
  inputValue: string;
  setInputValue: (val: string) => void;
  options: UserResponse[];
  selectedUsers: UserResponse[];
  handlePermissionChange: (
    userId: number,
    role: string,
    checked: boolean
  ) => void;
  handleRemoveConfirmation: (user: UserResponse | null) => void;
  handleAssign: () => void;
  handleSelect: (user: UserResponse) => void;
}

const AddUsersTab = ({
  inputValue,
  setInputValue,
  options,
  selectedUsers,
  handlePermissionChange,
  handleRemoveConfirmation,
  handleAssign,
  handleSelect,
}: Props) => {
  return (
    <div className="flex flex-col h-full justify-between">
      <div className="sticky top-0 bg-white z-10 px-4 py-2">
        <div className="relative mb-2">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
          />
        </div>

        {options.length > 0 && (
          <ul className="border rounded-md shadow max-h-48 overflow-y-auto">
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

      <PermisstionList
        selectedUsers={selectedUsers}
        handleRemoveConfirmation={handleRemoveConfirmation}
        handlePermissionChange={handlePermissionChange}
      />

      <div className="bg-white z-10 px-4 py-2 border-t">
        <button
          className="w-full bg-gray-800 text-white py-2 rounded hover:bg-gray-700 transition"
          onClick={handleAssign}
        >
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default AddUsersTab;
