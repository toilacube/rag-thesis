"use client";

import { Dispatch, SetStateAction } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/dialog";

interface Props {
  confirmUser: UserResponse;
  setConfirmUser: Dispatch<SetStateAction<UserResponse | null>>;
  handleRemove: (userId: number) => Promise<void>;
}
const RemoveConfirmation = ({
  confirmUser,
  setConfirmUser,
  handleRemove,
}: Props) => {
  return (
    <Dialog open={!!confirmUser} onOpenChange={() => setConfirmUser(null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove User</DialogTitle>
          <DialogDescription>
            Are you sure you want to remove <strong>{confirmUser.email}</strong>
            ?
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={() => setConfirmUser(null)}
            className="px-3 py-1 border rounded"
          >
            Cancel
          </button>
          <button
            onClick={async () => {
              if (!confirmUser) return;
              await handleRemove(confirmUser.id);
              setConfirmUser(null); // close dialog after delete
            }}
            className="px-3 py-1 bg-red-600 text-white rounded"
          >
            Confirm
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default RemoveConfirmation;
