"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/table";
import { useToast } from "@/components/use-toast";
import { APIKey } from "../api-keys";
import { toggleAPIKeyStatus } from "../utils/toggle-api-key-status";
import ApiKeysTableBody from "./api-keys-table-body";
import { deleteAPIKey } from "../utils/delete-api-key";

const ApiKeysTable = ({ initialApiKeys }: { initialApiKeys: APIKey[] }) => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>(initialApiKeys);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const { toast } = useToast();

  const handleDeleteAPIKey = async (id: number) => {
    try {
      await deleteAPIKey(id);

      setApiKeys(apiKeys.filter((key) => key.id !== id));
      toast({
        title: "Success",
        description: "API key deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete API key",
        variant: "destructive",
      });
    }
  };

  const handleToggleAPIKeyStatus = async (
    id: number,
    currentStatus: boolean
  ) => {
    try {
      await toggleAPIKeyStatus(id, currentStatus);

      setApiKeys(
        apiKeys.map((key) =>
          key.id === id ? { ...key, is_active: !currentStatus } : key
        )
      );

      toast({
        title: "Success",
        description: "API key status updated successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to update API key",
        variant: "destructive",
      });
    }
  };

  const handleCopyAPIKey = async (id: number, key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedId(id);
      setTimeout(() => {
        setCopiedId(null);
      }, 3000);
      toast({
        title: "Success",
        description: "API key copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy API key",
        variant: "destructive",
      });
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>API Key</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Last Used</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <ApiKeysTableBody
          apiKeys={apiKeys}
          copiedId={copiedId}
          deleteAPIKey={handleDeleteAPIKey}
          toggleAPIKeyStatus={handleToggleAPIKeyStatus}
          copyAPIKey={handleCopyAPIKey}
        />
      </TableBody>
    </Table>
  );
};

export default ApiKeysTable;
