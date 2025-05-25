"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export interface Chat {
    id: number;
    title: string;
    project_id: number;
    created_at: string;
    updated_at: string;
    messages: any[];
}

interface ChatContextType {
    chats: Chat[];
    setChats: (chats: Chat[]) => void;
    selectedChat: Chat | null;
    setSelectedChat: (chat: Chat | null) => void;
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;
    searchTerm: string;
    setSearchTerm: (searchTerm: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({
    children,
    initialChats = [],
    initialSelectedChat = null,
    initialIsLoading = false,
}: {
    children: ReactNode;
    initialChats?: Chat[];
    initialSelectedChat?: Chat | null;
    initialIsLoading?: boolean;
}) {
    const [chats, setChats] = useState<Chat[]>(initialChats);
    const [selectedChat, setSelectedChat] = useState<Chat | null>(initialSelectedChat);
    const [isLoading, setIsLoading] = useState(initialIsLoading);
    const [searchTerm, setSearchTerm] = useState("");
    return (
        <ChatContext.Provider
            value={{ chats, setChats, selectedChat, setSelectedChat, isLoading, setIsLoading, searchTerm, setSearchTerm }}
        >
            {children}
        </ChatContext.Provider>
    );
}

export function useChat() {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
}
