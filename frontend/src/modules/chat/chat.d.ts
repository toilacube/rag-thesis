
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