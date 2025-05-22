"use client";

import { logout } from "./utils";
import { FaSignOutAlt } from "react-icons/fa";

const Logout = () => {
  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="border-t p-4 space-y-4">
      <button
        onClick={handleLogout}
        className="flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors duration-200"
      >
        <FaSignOutAlt className="mr-3 h-4 w-4" />
        Sign out
      </button>
    </div>
  );
};

export default Logout;
