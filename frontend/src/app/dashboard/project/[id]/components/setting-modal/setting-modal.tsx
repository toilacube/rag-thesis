"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/dialog";
import { FaCog } from "react-icons/fa";
import UserAssignment from "./user-assignment";

export default function SettingModal() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <FaCog
        size={24}
        onClick={() => setOpen(true)}
        className="cursor-pointer text-gray-600 hover:text-gray-800"
      />

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Settings</DialogTitle>
          </DialogHeader>
          <div className="text-sm text-gray-700">
            <UserAssignment />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
