"use client";
import { FiSearch } from "react-icons/fi";
import { useChat } from "@/contexts/chat-provider";

const ChatSearch = () => {
    const { searchTerm, setSearchTerm } = useChat();
    return (<div className="relative">
        <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-full border bg-background/50 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
        />
    </div>)
};

export default ChatSearch;