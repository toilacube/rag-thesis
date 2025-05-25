"use client";

import { FiCopy, FiCheck } from "react-icons/fi";
import { Button } from "@/components/button";
import { Switch } from "@/components/switch";
import { TableCell, TableRow } from "@/components/table";
import { APIKey } from "../api-keys";

const ApiKeysTableBody = ({
  apiKeys,
  copiedId,
  deleteAPIKey,
  toggleAPIKeyStatus,
  copyAPIKey,
}: {
  apiKeys: APIKey[];
  copiedId: number | null;
  deleteAPIKey: (id: number) => void;
  toggleAPIKeyStatus: (id: number, currentStatus: boolean) => void;
  copyAPIKey: (id: number, key: string) => void;
}) => {
  if (apiKeys.length === 0) {
    return (
      <TableRow>
        <TableCell colSpan={6} className="text-center">
          No API keys found
        </TableCell>
      </TableRow>
    );
  }

  return apiKeys.map((apiKey) => (
    <TableRow key={apiKey.id}>
      <TableCell>{apiKey.name}</TableCell>
      <TableCell className="flex items-center gap-2">
        <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm">
          {apiKey.key}
        </code>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => copyAPIKey(apiKey.id, apiKey.key)}
        >
          {copiedId === apiKey.id ? (
            <FiCheck className="h-4 w-4" />
          ) : (
            <FiCopy className="h-4 w-4" />
          )}
        </Button>
      </TableCell>
      <TableCell>
        <Switch
          checked={apiKey.is_active}
          onCheckedChange={() =>
            toggleAPIKeyStatus(apiKey.id, apiKey.is_active)
          }
        />
      </TableCell>
      <TableCell>{new Date(apiKey.created_at).toLocaleDateString()}</TableCell>
      <TableCell>
        {apiKey.last_used_at
          ? new Date(apiKey.last_used_at).toLocaleDateString()
          : "Never"}
      </TableCell>
      <TableCell>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => deleteAPIKey(apiKey.id)}
        >
          Delete
        </Button>
      </TableCell>
    </TableRow>
  ));
};

export default ApiKeysTableBody;
