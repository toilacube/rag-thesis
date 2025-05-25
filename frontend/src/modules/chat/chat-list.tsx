'use client';

import { FiMessageSquare, FiPlus, FiTrash2 } from "react-icons/fi";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Chat, useChat } from "@/contexts/chat-provider";
import { toast } from "@/components/use-toast";
import { ApiError } from "@/lib/api";
import { useEffect } from "react";
import { getChatList } from "./utils/get-chat-list";

const ChatList = () => {
    const { chats, setChats, searchTerm } = useChat();

    useEffect(() => {
        fetchChats();
    }, []);

    const fetchChats = async () => {
        const chats = await getChatList();
        setChats(chats);
    }

    const filteredChats = chats.filter((chat) =>
        chat.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleDelete = async (chatId: number) => {
        if (!confirm("Are you sure you want to delete this chat session?")) return;
        try {
            // Assuming a DELETE /api/chat/{chat_id} endpoint exists (not in provided doc, but common)
            // If not, this functionality needs backend support.
            // For now, we'll remove it from the list optimistically if no delete endpoint.
            // await api.delete(`/api/chat/${chatId}`);

            setChats(chats.filter((chat) => chat.id !== chatId));
            toast({
                title: "Chat Deleted",
                description: "Chat session has been removed (locally).", // Adjust if API delete is implemented
            });
        } catch (error) {
            console.error("Failed to delete chat:", error);
            toast({
                title: "Error",
                description:
                    error instanceof ApiError ? error.message : "Could not delete chat.",
                variant: "destructive",
            });
        }
    };

    if (chats.length === 0) {
        return (
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
        )
    }

    return (
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
                                    <h3
                                        className="font-semibold text-lg truncate group-hover:text-primary transition-colors"
                                        title={chat.title}
                                    >
                                        {chat.title}
                                    </h3>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {chat.messages.length} messages â€¢ Updated{" "}
                                        {formatDistanceToNow(new Date(chat.updated_at), {
                                            addSuffix: true,
                                        })}
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
    )
};

export default ChatList;