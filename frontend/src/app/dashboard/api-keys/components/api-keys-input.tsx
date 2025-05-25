"use client";

import { useState } from "react";
import { FiPlus, FiList } from "react-icons/fi";
import { Button } from "@/components/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/dialog";
import { Input } from "@/components/input";
import { Label } from "@/components/label";
import { useToast } from "@/components/use-toast";
import { APIKey } from "../api-keys";
import { createAPIKey } from "../utils/create-api-key";

const ApiKeyInput = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isAPIListDialogOpen, setIsAPIListDialogOpen] = useState(false);
  const { toast } = useToast();

  const handleCreateAPIKey = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a name for the API key",
        variant: "destructive",
      });
      return;
    }

    setIsCreating(true);
    try {
      const data = await createAPIKey(newKeyName);

      setApiKeys([...apiKeys, data]);
      setNewKeyName("");
      setIsDialogOpen(false);
      toast({
        title: "Success",
        description: "API key created successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create API key",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };
  return (
    <div className="flex justify-between items-center mb-8">
      <h1 className="text-2xl font-bold">API Keys</h1>
      <div className="flex gap-4">
        <Dialog
          open={isAPIListDialogOpen}
          onOpenChange={setIsAPIListDialogOpen}
        >
          <DialogTrigger asChild>
            <Button variant="outline">
              <FiList className="mr-2 h-4 w-4" />
              API List
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Available API Endpoints</DialogTitle>
              <DialogDescription>
                List of available API endpoints and their usage.
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4 space-y-6">
              <div className="border rounded-lg p-6 bg-slate-50">
                <h3 className="text-lg font-semibold mb-4">
                  Knowledge Base Query
                </h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">
                      Method
                    </h4>
                    <code className="block p-3 bg-white border rounded-md text-sm font-mono text-blue-600">
                      GET
                    </code>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">
                      Endpoint
                    </h4>
                    <code className="block p-3 bg-white border rounded-md text-sm font-mono">
                      /openapi/knowledge/{"{id}"}/query
                    </code>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">
                      Query Parameters
                    </h4>
                    <div className="bg-white border rounded-md p-3 space-y-2">
                      <div className="grid grid-cols-3 text-sm">
                        <div className="font-mono text-blue-600">query</div>
                        <div className="col-span-2">
                          Your search query string
                        </div>
                      </div>
                      <div className="grid grid-cols-3 text-sm">
                        <div className="font-mono text-blue-600">top_k</div>
                        <div className="col-span-2">
                          Number of results to return (optional, default: 3)
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-2">
                      Headers
                    </h4>
                    <div className="bg-white border rounded-md p-3 grid grid-cols-3 text-sm">
                      <div className="font-mono text-blue-600">X-API-Key</div>
                      <div className="col-span-2">your_api_key</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <FiPlus className="mr-2 h-4 w-4" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key to access the API programmatically.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="Enter API key name"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreateAPIKey}
                disabled={isCreating || !newKeyName.trim()}
              >
                {isCreating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ApiKeyInput;
