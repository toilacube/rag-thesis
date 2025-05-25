import Link from "next/link";
import { FiPlus } from "react-icons/fi";
import ChatSearch from "./chat-search";
import ChatList from "./chat-list";

const Chat = async () => {
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
          <ChatSearch />
        </div>
      </div>

      <ChatList />
    </div>
  );
}

export default Chat;