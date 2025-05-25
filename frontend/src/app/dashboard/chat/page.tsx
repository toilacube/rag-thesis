import { ChatProvider } from "@/contexts/chat-provider";
import { Chat } from "@/modules/chat";

const Page = async () => {
  return (
    <ChatProvider initialChats={[]}>
      <Chat />
    </ChatProvider>
  );
}

export default Page;