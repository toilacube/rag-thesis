"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FiPlus, FiMessageSquare, FiTrash2, FiSearch } from "react-icons/fi";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/use-toast";
import { formatDistanceToNow } from "date-fns"; // For better date display

// Updated interfaces to match API DTOs
interface MessageResponse {
  content: string;
  role: "user" | "assistant";
  id: number;
  chat_id: number;
  created_at: string;
  updated_at: string;
}

interface ChatResponse {
  title: string;
  id: number;
  user_id: number;
  project_id: number;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

export default function ChatListPage() { // Renamed for clarity
  const [chats, setChats] = useState<ChatResponse[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    setIsLoading(true);
    try {
      const data = await api.get("/api/chat/");
      setChats(data);
    } catch (error) {
      console.error("Failed to fetch chats:", error);
      toast({
        title: "Error",
        description: error instanceof ApiError ? error.message : "Could not load chats.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (chatId: number) => {
    if (!confirm("Are you sure you want to delete this chat session?")) return;
    try {
      // Assuming a DELETE /api/chat/{chat_id} endpoint exists (not in provided doc, but common)
      // If not, this functionality needs backend support.
      // For now, we'll remove it from the list optimistically if no delete endpoint.
      // await api.delete(`/api/chat/${chatId}`);

      setChats((prevChats) => prevChats.filter((chat) => chat.id !== chatId));
      toast({
        title: "Chat Deleted",
        description: "Chat session has been removed (locally).", // Adjust if API delete is implemented
      });
    } catch (error) {
      console.error("Failed to delete chat:", error);
      toast({
        title: "Error",
        description: error instanceof ApiError ? error.message : "Could not delete chat.",
        variant: "destructive",
      });
    }
  };

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-card rounded-lg shadow-sm p-6 animate-pulse">
          <div className="h-8 w-3/4 bg-muted rounded mb-2"></div>
          <div className="h-6 w-1/2 bg-muted rounded"></div>
        </div>
        {/* Add more skeleton loaders if desired */}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-card rounded-lg shadow-sm p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Your Conversations
            </h2>
            <p className="text-muted-foreground mt-1">
              Explore and manage your chat history
            </p>
          </div>
          <Link
            href="/dashboard/chat/new"
            className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors duration-200 shadow-sm hover:shadow-md"
          >
            <FiPlus className="mr-2 h-4 w-4" />
            Start New Chat
          </Link>
        </div>

        <div className="mt-6 relative">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-full border bg-background/50 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredChats.map((chat) => (
          <div
            key={chat.id}
            className="group relative bg-card rounded-xl border shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
          >
            <Link href={`/dashboard/chat/${chat.id}`} className="block h-full">
              <div className="p-5 flex flex-col h-full">
                <div className="flex items-start gap-4">
                  <div className="bg-primary/10 rounded-lg p-2">
                    <FiMessageSquare className="h-6 w-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-lg truncate group-hover:text-primary transition-colors" title={chat.title}>
                      {chat.title}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {chat.messages.length} messages â€¢ Updated {formatDistanceToNow(new Date(chat.updated_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                {chat.messages.length > 0 && (
                  <p className="text-sm text-muted-foreground mt-4 line-clamp-2 flex-grow">
                    {chat.messages[chat.messages.length - 1].content}
                  </p>
                )}
                 {chat.messages.length === 0 && (
                    <p className="text-sm text-muted-foreground mt-4 italic flex-grow">
                        No messages yet.
                    </p>
                )}
              </div>
            </Link>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent link navigation
                handleDelete(chat.id);
              }}
              title="Delete chat"
              className="absolute top-3 right-3 p-1.5 rounded-full hover:bg-destructive/10 group/delete z-10"
            >
              <FiTrash2 className="h-4 w-4 text-muted-foreground group-hover/delete:text-destructive transition-colors" />
            </button>
          </div>
        ))}
      </div>

      {!isLoading && chats.length === 0 && (
        <div className="text-center py-16 bg-card rounded-lg border">
          <FiMessageSquare className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <h3 className="mt-4 text-lg font-medium text-foreground">
            No conversations yet
          </h3>
          <p className="mt-2 text-muted-foreground">
            Start a new chat to begin exploring your knowledge base
          </p>
          <Link
            href="/dashboard/chat/new"
            className="mt-6 inline-flex items-center justify-center rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors duration-200"
          >
            <FiPlus className="mr-2 h-4 w-4" />
            Start Your First Chat
          </Link>
        </div>
      )}
    </div>
  );
}