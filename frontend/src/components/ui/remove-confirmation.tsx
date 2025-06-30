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
  id: number;
  setId: Dispatch<SetStateAction<number | null>>;
  handleRemove: (Id: number) => Promise<void>;
}
const RemoveConfirmation = ({ id, setId, handleRemove }: Props) => {
  return (
    <Dialog open={!!id} onOpenChange={(isOpen) => !isOpen && setId(null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove</DialogTitle>
          <DialogDescription>
            Are you sure you want to remove?
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={() => setId(null)}
            className="px-3 py-1 border rounded"
          >
            Cancel
          </button>
          <button
            onClick={async () => {
              if (!id) return;
              await handleRemove(id);
              setId(null); // close dialog after delete
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
