"use client";

import React, { useEffect, useRef, useState, FormEvent, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { FiSend, FiUser, FiCopy, FiCheck, FiLoader } from "react-icons/fi";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Button } from "@/components/button";
import { Skeleton } from "@/components/skeleton";

interface Message {
  id: number;
  content: string;
  role: "user" | "assistant";
  chat_id?: number;
  created_at?: string;
  updated_at?: string;
  isStreaming?: boolean; // Still useful for styling the streaming message
  tempId?: string; // For optimistic user messages and the streaming assistant message
}

interface ChatSession {
  title: string;
  id: number;
  user_id: number;
  project_id: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

// SSE Event Data Structures remain the same
interface UserMessageSavedEvent { type: "user_message_saved"; message: Message; }
interface DeltaEvent { type: "delta"; content: string; }
interface AssistantMessageSavedEvent { type: "assistant_message_saved"; message: Message; }
interface ErrorEvent { type: "error"; detail: string; status_code?: number; }
interface StreamEndEvent { type: "stream_end"; }

type SSEEventData =
  | UserMessageSavedEvent
  | DeltaEvent
  | AssistantMessageSavedEvent
  | ErrorEvent
  | StreamEndEvent;

export default function ChatInterfacePage() {
  const params = useParams();
  const chatId = params.id as string;
  const router = useRouter();
  const { toast } = useToast();

  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  // New state for the currently streaming assistant message
  const [streamingAssistantMessage, setStreamingAssistantMessage] = useState<Message | null>(null);
  const [input, setInput] = useState("");
  const [isLoadingStream, setIsLoadingStream] = useState(false); // True when waiting for or processing stream
  const [isFetchingHistory, setIsFetchingHistory] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);
  
  const copyToClipboard = async (text: string, keySuffix: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(keySuffix);
      toast({ title: "Copied!", description: "Message ID copied to clipboard." });
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      toast({ title: "Copy Failed", description: "Could not copy text.", variant: "destructive" });
    }
  };

  useEffect(() => {
    const fetchChatHistory = async () => {
      if (!chatId) return;
      setIsFetchingHistory(true);
      try {
        const data: ChatSession = await api.get(`/api/chat/${chatId}`);
        setChatSession(data);
        setMessages(data.messages || []);
      } catch (error) {
        console.error("Failed to fetch chat history:", error);
        toast({
          title: "Error Loading Chat",
          description: error instanceof ApiError ? error.message : "Could not load chat history.",
          variant: "destructive",
        });
        router.push("/dashboard/chat");
      } finally {
        setIsFetchingHistory(false);
      }
    };
    fetchChatHistory();
  }, [chatId, router, toast]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingAssistantMessage, scrollToBottom]); // Also scroll when streaming message appears/updates

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);


  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoadingStream) return;

    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    setStreamingAssistantMessage(null); // Clear any previous streaming message

    const optimisticUserMessage: Message = {
      id: 0,
      tempId: `user-${crypto.randomUUID()}`,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages((prevMessages) => [...prevMessages, optimisticUserMessage]);
    const currentInput = input;
    setInput("");
    setIsLoadingStream(true);
    
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
    if (!token) {
        toast({title: "Authentication Error", description: "No authentication token found.", variant: "destructive"});
        setIsLoadingStream(false);
        setMessages(prev => prev.filter(msg => msg.tempId !== optimisticUserMessage.tempId));
        return;
    }

    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || `http://${process.env.BACKEND_SERVER || 'localhost'}:${process.env.BACKEND_PORT || '8000'}/api`}/chat/${chatId}/message`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({ content: currentInput, role: "user" }),
            signal: abortControllerRef.current.signal,
        });

        if (!response.ok || !response.body) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown server error." }));
            throw new ApiError(response.status, errorData.detail || errorData.message || "Failed to send message.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        
        // eslint-disable-next-line no-constant-condition
        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                if (isLoadingStream) setIsLoadingStream(false); // If stream ends without stream_end event
                // If streamingAssistantMessage is still populated here, it means an incomplete stream.
                // Add it to messages if it has content.
                if (streamingAssistantMessage && streamingAssistantMessage.content.trim()) {
                    setMessages(prev => [...prev, { ...streamingAssistantMessage, isStreaming: false }]);
                }
                setStreamingAssistantMessage(null);
                abortControllerRef.current = null;
                break;
            }
            buffer += decoder.decode(value, { stream: true });
        
            let eolIndex;
            while ((eolIndex = buffer.indexOf('\n\n')) >= 0) {
                const eventString = buffer.substring(0, eolIndex).trim();
                buffer = buffer.substring(eolIndex + 2);
        
                if (eventString.startsWith("data: ")) {
                    try {
                        const jsonData: SSEEventData = JSON.parse(eventString.substring(6));
                
                        if (jsonData.type === "user_message_saved") {
                            setMessages(prev => prev.map(msg => 
                                msg.tempId === optimisticUserMessage.tempId 
                                ? { ...jsonData.message, tempId: undefined }
                                : msg
                            ));
                        } else if (jsonData.type === "delta") {
                            setStreamingAssistantMessage(prevStreamingMsg => {
                                if (!prevStreamingMsg) { // First delta
                                    return {
                                        id: 0, // Placeholder
                                        tempId: `assistant-${crypto.randomUUID()}`,
                                        role: "assistant",
                                        content: jsonData.content,
                                        isStreaming: true,
                                        created_at: new Date().toISOString(),
                                    };
                                }
                                // Subsequent deltas
                                return {
                                    ...prevStreamingMsg,
                                    content: (prevStreamingMsg.content || "") + jsonData.content,
                                };
                            });
                        } else if (jsonData.type === "assistant_message_saved") {
                            setMessages(prev => [...prev, { ...jsonData.message, isStreaming: false, tempId: undefined }]);
                            setStreamingAssistantMessage(null); // Clear streaming message
                        } else if (jsonData.type === "error") {
                            toast({ title: "Stream Error", description: jsonData.detail, variant: "destructive" });
                            // Optionally, add error to the streaming message or messages list
                            if (streamingAssistantMessage) {
                                setStreamingAssistantMessage(prev => prev ? {...prev, content: `${prev.content}\n\n[Error: ${jsonData.detail}]`, isStreaming: false} : null);
                            } else {
                                // If error before any delta, you might add a new error message to `messages`
                            }
                            setIsLoadingStream(false);
                        } else if (jsonData.type === "stream_end") {
                            setIsLoadingStream(false);
                            // If streamingAssistantMessage is still populated (e.g. error occurred but no assistant_message_saved)
                            // we ensure it's added to messages if it has content and then cleared.
                            if (streamingAssistantMessage && streamingAssistantMessage.content.trim()) {
                                 setMessages(prev => [...prev, { ...streamingAssistantMessage, isStreaming: false }]);
                            }
                            setStreamingAssistantMessage(null);
                            abortControllerRef.current = null;
                            return; 
                        }
                    } catch (e) {
                        console.error("Error parsing SSE JSON:", e, "Raw event string:", eventString);
                    }
                } else if (eventString.trim()) {
                    console.log("Received non-data SSE line:", eventString);
                }
            }
        }
    } catch (err) {
        if ((err as Error).name === 'AbortError') {
            console.log('SSE Fetch aborted.');
            setMessages(prev => prev.filter(msg => msg.tempId !== optimisticUserMessage.tempId));
            setStreamingAssistantMessage(null); // Clear if aborted
        } else {
            console.error("Error in handleSubmit:", err);
            const apiErr = err as ApiError;
            toast({
                title: "Message Error",
                description: apiErr.message || (err as Error).message || "Could not send message.",
                variant: "destructive",
            });
            setMessages(prev => prev.filter(msg => msg.tempId !== optimisticUserMessage.tempId));
        }
    } finally {
        // General cleanup if isLoadingStream is true but stream might have ended without explicit 'stream_end'
        // or if an error didn't set it to false.
        if (isLoadingStream) {
          setIsLoadingStream(false);
        }
        // Handled by stream_end or explicit setting now.
        // If streamingAssistantMessage is still present at the very end of an abnormal exit,
        // it might be an incomplete message. The logic in `done` and `stream_end` tries to handle this.
    }
  };

  if (isFetchingHistory) {
    return (
        <div className="flex flex-col h-[calc(100vh-5rem)] relative p-4 space-y-4">
            <Skeleton className="h-8 w-3/4 self-start rounded-lg" />
            <Skeleton className="h-12 w-1/2 self-end rounded-lg" />
            <Skeleton className="h-10 w-2/3 self-start rounded-lg" />
            <div className="mt-auto flex items-center space-x-4">
                <Skeleton className="h-10 flex-1 rounded-md" />
                <Skeleton className="h-10 w-10 rounded-md" />
            </div>
        </div>
    );
  }

  if (!chatSession) {
    return <div className="p-4 text-center">Chat session not found or could not be loaded.</div>;
  }
  
  // Helper to render a single message (used for historical and the live streaming one)
  const renderMessage = (message: Message, isLiveStreaming: boolean = false) => {
    const messageKey = message.tempId || `${message.role}-${message.id}`;
    const displayId = (!message.tempId && message.id !== 0) ? message.id.toString() : (message.tempId ? '(pending)' : '(error)');
    
    return (
      <div
        key={messageKey}
        className={`flex items-end space-x-2 group ${
          message.role === "user" ? "justify-end" : "justify-start"
        }`}
      >
        {message.role === "assistant" && (
          <div className="w-8 h-8 flex-shrink-0 flex items-center justify-center self-start mt-1">
            <img src="/logo.png" className="h-7 w-7 rounded-full object-cover" alt="AI Assistant" />
          </div>
        )}
        <div
          className={`max-w-[80%] rounded-lg px-3 py-2 shadow-sm prose prose-sm dark:prose-invert ${
            message.role === "user"
              ? "bg-primary text-primary-foreground"
              : "bg-background text-foreground border"
          }`}
        >
          {message.role === "assistant" || (message.role === "user" && message.content.includes("```")) ? ( // Render user message as markdown if it contains code blocks
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                {message.content}
            </ReactMarkdown>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}

          {(isLiveStreaming || message.isStreaming) && ( // Show streaming indicator
            <div className="flex items-center space-x-1 pt-1 text-xs text-muted-foreground">
              <FiLoader className="w-3 h-3 animate-spin" />
              <span>Streaming...</span>
            </div>
          )}
          <div className="text-xs mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2"
              title={message.created_at ? new Date(message.created_at).toLocaleString() : 'Sending...'}>
            <span className={message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"}>
                ID: {displayId}
            </span>
            {!message.tempId && message.id !== 0 && (
                <Button variant="ghost" size="icon" className="h-5 w-5 p-0" onClick={() => copyToClipboard(message.id.toString(), message.id.toString())}>
                    {copiedId === message.id.toString() ? <FiCheck className="h-3 w-3"/> : <FiCopy className="h-3 w-3"/>}
                </Button>
            )}
          </div>
        </div>
        {message.role === "user" && (
          <div className="w-8 h-8 rounded-full bg-primary flex-shrink-0 items-center justify-center text-primary-foreground self-start mt-1">
            <FiUser className="h-5 w-5" />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] relative bg-muted/20">
        <div className="p-4 border-b bg-background shadow-sm">
            <h1 className="text-xl font-semibold truncate" title={chatSession.title}>{chatSession.title}</h1>
        </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-6 pb-[100px]">
        {messages.map((message) => renderMessage(message, false))}
        {streamingAssistantMessage && renderMessage(streamingAssistantMessage, true)}
        <div ref={messagesEndRef} />
      </div>
      <form
        onSubmit={handleSubmit}
        className="border-t p-4 flex items-center space-x-2 sm:space-x-4 bg-background absolute bottom-0 left-0 right-0 shadow-md"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoadingStream || isFetchingHistory}
          className="flex-1 min-w-0 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-70"
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e as any); 
            }
          }}
        />
        <Button
          type="submit"
          disabled={isLoadingStream || isFetchingHistory || !input.trim()}
          className="h-10 px-4 py-2"
        >
          {isLoadingStream ? (
            <FiLoader className="h-4 w-4 animate-spin" />
          ) : (
            <FiSend className="h-4 w-4" />
          )}
        </Button>
      </form>
    </div>
  );
}