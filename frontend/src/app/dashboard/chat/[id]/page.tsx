"use client";

import React, {
  useEffect,
  useRef,
  useState,
  FormEvent,
  useCallback,
} from "react";
import { useParams, useRouter } from "next/navigation";
import { FiSend, FiUser, FiCopy, FiCheck, FiLoader } from "react-icons/fi";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// --- Type Definitions ---
interface Message {
  id: number;
  content: string;
  role: "user" | "assistant";
  chat_id?: number;
  created_at?: string;
  updated_at?: string;
  isStreaming?: boolean;
  tempId?: string;
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

// --- SSE Event Types ---
interface UserMessageSavedEvent {
  type: "user_message_saved";
  message: Message;
}
interface DeltaEvent {
  type: "delta";
  content: string;
}
interface AssistantMessageSavedEvent {
  type: "assistant_message_saved";
  message: Message;
}
interface ErrorEvent {
  type: "error";
  detail: string;
  status_code?: number;
}
interface StreamEndEvent {
  type: "stream_end";
}
interface CitationPayloadEvent {
  type: "citation_payload";
  data: string;
} // data is base64 string

type SSEEventData =
  | UserMessageSavedEvent
  | DeltaEvent
  | AssistantMessageSavedEvent
  | ErrorEvent
  | StreamEndEvent
  | CitationPayloadEvent;

// --- Citation Context Type ---
interface CitationContext {
  page_content: string;
  metadata: {
    document_id?: string | number;
    project_id?: string | number;
    file_name?: string;
    chunk_id?: string;
    headers?: Record<string, string>;
  };
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  `http://${process.env.NEXT_PUBLIC_BACKEND_SERVER || "localhost"}:${
    process.env.NEXT_PUBLIC_BACKEND_PORT || "8000"
  }/api`;

export default function ChatInterfacePage() {
  const params = useParams();
  const chatId = params.id as string;
  const router = useRouter();
  const { toast } = useToast();

  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingAssistantMessage, setStreamingAssistantMessage] =
    useState<Message | null>(null);
  const [input, setInput] = useState("");
  const [isLoadingStream, setIsLoadingStream] = useState(false);
  const [isFetchingHistory, setIsFetchingHistory] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [citationContexts, setCitationContexts] = useState<CitationContext[]>(
    [],
  );
  const [selectedCitation, setSelectedCitation] =
    useState<CitationContext | null>(null);
  const [isCitationDialogOpen, setIsCitationDialogOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const copyToClipboard = useCallback(
    async (text: string, messageIdOrContent: string) => {
      try {
        await navigator.clipboard.writeText(text); // Copy the actual content
        setCopiedId(messageIdOrContent); // Use message ID or a unique part of content as key
        toast({
          title: "Copied!",
          description: "Message content copied to clipboard.",
        });
        setTimeout(() => setCopiedId(null), 2000);
      } catch (err) {
        toast({
          title: "Copy Failed",
          description: "Could not copy text.",
          variant: "destructive",
        });
      }
    },
    [toast],
  );

  useEffect(() => {
    if (!chatId) return;
    const fetchChatHistory = async () => {
      setIsFetchingHistory(true);
      try {
        const data: ChatSession = await api.get(`/api/chat/${chatId}`);
        setChatSession(data);
        setMessages(data.messages || []);
      } catch (error) {
        console.error("Failed to fetch chat history:", error);
        toast({
          title: "Error Loading Chat",
          description:
            error instanceof ApiError
              ? error.message
              : "Could not load chat history.",
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
  }, [messages, streamingAssistantMessage, scrollToBottom]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const markdownParseWithCitations = (text: string): string => {
    if (!text) return "";
    return text
      .replace(/\[\[([cC])itation/g, "[citation")
      .replace(/[cC]itation:(\d+)]]/g, "citation:$1]")
      .replace(/\[\[([cC]itation:\d+)]](?!])/g, `[$1]`)
      .replace(/\[[cC]itation:(\d+)]/g, "[citation]($1)");
  };

  const handleSubmit = async (
    e: FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLInputElement>,
  ) => {
    // Adjusted type for onKeyPress
    e.preventDefault();
    if (!input.trim() || isLoadingStream) return;

    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setCitationContexts([]); // Clear previous citation contexts
    setStreamingAssistantMessage(null);

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

    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) {
      toast({
        title: "Authentication Error",
        description: "No authentication token found.",
        variant: "destructive",
      });
      setIsLoadingStream(false);
      setMessages((prev) =>
        prev.filter((msg) => msg.tempId !== optimisticUserMessage.tempId),
      );
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/${chatId}/message`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ content: currentInput, role: "user" }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok || !response.body) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Unknown server error." }));
        throw new ApiError(
          response.status,
          errorData.detail || errorData.message || "Failed to send message.",
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (isLoadingStream) setIsLoadingStream(false);
          if (
            streamingAssistantMessage &&
            streamingAssistantMessage.content.trim()
          ) {
            setMessages((prev) => [
              ...prev,
              {
                ...streamingAssistantMessage,
                isStreaming: false,
                tempId: undefined,
              },
            ]);
          }
          setStreamingAssistantMessage(null);
          abortControllerRef.current = null;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        let eolIndex;
        while ((eolIndex = buffer.indexOf("\n\n")) >= 0) {
          const eventString = buffer.substring(0, eolIndex).trim();
          buffer = buffer.substring(eolIndex + 2);

          if (eventString.startsWith("data: ")) {
            try {
              const jsonData: SSEEventData = JSON.parse(
                eventString.substring(6),
              );

              // YOUR ORIGINAL SSE LOGIC STYLE + CITATION_PAYLOAD
              if (jsonData.type === "user_message_saved") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.tempId === optimisticUserMessage.tempId
                      ? { ...jsonData.message, tempId: undefined }
                      : msg,
                  ),
                );
              } else if (jsonData.type === "citation_payload") {
                try {
                  const jsonString = atob(jsonData.data);
                  const parsedData = JSON.parse(jsonString);
                  if (parsedData.context && Array.isArray(parsedData.context)) {
                    setCitationContexts(parsedData.context);
                  } else {
                    console.warn(
                      "Received citation_payload with invalid structure:",
                      parsedData,
                    );
                    toast({
                      title: "Citation Warning",
                      description:
                        "Received malformed citation data from server.",
                      variant: "default",
                    });
                  }
                } catch (error) {
                  console.error(
                    "Error decoding/parsing citation_payload:",
                    error,
                    "Raw data:",
                    jsonData.data,
                  );
                  toast({
                    title: "Citation Error",
                    description: "Could not process citation data.",
                    variant: "destructive",
                  });
                }
              } else if (jsonData.type === "delta") {
                setStreamingAssistantMessage((prevStreamingMsg) => {
                  if (!prevStreamingMsg) {
                    return {
                      id: 0,
                      tempId: `assistant-${crypto.randomUUID()}`,
                      role: "assistant",
                      content: jsonData.content,
                      isStreaming: true,
                      created_at: new Date().toISOString(),
                    };
                  }
                  return {
                    ...prevStreamingMsg,
                    content:
                      (prevStreamingMsg.content || "") + jsonData.content,
                  };
                });
              } else if (jsonData.type === "assistant_message_saved") {
                setMessages((prev) => [
                  ...prev,
                  {
                    ...jsonData.message,
                    isStreaming: false,
                    tempId: undefined,
                  },
                ]);
                setStreamingAssistantMessage(null);
              } else if (jsonData.type === "error") {
                toast({
                  title: "Stream Error",
                  description: jsonData.detail,
                  variant: "destructive",
                });
                if (streamingAssistantMessage) {
                  setStreamingAssistantMessage((prev) =>
                    prev
                      ? {
                          ...prev,
                          content: `${prev.content || ""}\n\n[Stream Error: ${
                            jsonData.detail
                          }]`,
                          isStreaming: false,
                        }
                      : null,
                  );
                }
                // setIsLoadingStream(false); // stream_end should handle this
              } else if (jsonData.type === "stream_end") {
                setIsLoadingStream(false);
                if (
                  streamingAssistantMessage &&
                  streamingAssistantMessage.content.trim()
                ) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      ...streamingAssistantMessage,
                      isStreaming: false,
                      tempId: undefined,
                    },
                  ]);
                }
                setStreamingAssistantMessage(null);
                abortControllerRef.current = null;
                reader.cancel(); // Cancel the reader as stream is declared ended by server
                return;
              }
            } catch (parseError) {
              console.error(
                "Error parsing SSE JSON:",
                parseError,
                "Raw event string:",
                eventString,
              );
            }
          } else if (eventString.trim()) {
            console.log("Received non-data SSE line:", eventString);
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        console.log("SSE Fetch aborted.");
        // Only remove optimistic user message if it wasn't confirmed by "user_message_saved"
        // This might be complex to track perfectly without more state.
        // For simplicity, if aborted, we assume user message might not be on server.
        setMessages((prev) =>
          prev.filter((msg) => msg.tempId !== optimisticUserMessage.tempId),
        );
        setStreamingAssistantMessage(null);
      } else {
        console.error("Error in handleSubmit streaming:", err);
        const apiErr = err as ApiError;
        toast({
          title: "Message Error",
          description:
            apiErr.message ||
            (err as Error).message ||
            "Could not send message.",
          variant: "destructive",
        });
        setMessages((prev) =>
          prev.filter((msg) => msg.tempId !== optimisticUserMessage.tempId),
        );
      }
    } finally {
      if (isLoadingStream) {
        setIsLoadingStream(false);
      }
    }
  };

  const handleCitationClick = (citationNumber: number) => {
    const index = citationNumber - 1;
    if (citationContexts && index >= 0 && index < citationContexts.length) {
      setSelectedCitation(citationContexts[index]);
      setIsCitationDialogOpen(true);
    } else {
      console.warn(
        `Clicked citation [${citationNumber}], but no corresponding context found.`,
      );
      toast({
        title: "Citation Not Found",
        description: `Details for citation ${citationNumber} are not available.`,
        variant: "default",
      });
    }
  };

  const renderMessage = (
    message: Message,
    isLiveStreaming: boolean = false,
  ) => {
    const messageKey =
      message.tempId || `${message.role}-${message.id || crypto.randomUUID()}`; // Ensure key even if id is 0
    const displayId =
      !message.tempId && message.id !== 0
        ? message.id.toString()
        : message.tempId
          ? "(sending)"
          : "(streaming)";

    const isUser = message.role === "user";
    const avatar = isUser ? (
      <div className="w-8 h-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center text-primary-foreground self-start mt-1">
        <FiUser className="h-5 w-5" />
      </div>
    ) : (
      <div className="w-8 h-8 flex-shrink-0 flex items-center justify-center self-start mt-1">
        <img
          src="/logo.png"
          className="h-7 w-7 rounded-full object-cover"
          alt="AI"
        />
      </div>
    );

    const messageContent = (
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 shadow-sm prose prose-sm dark:prose-invert ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-background text-foreground border"
        }`}
      >
        {message.role === "assistant" ||
        (isUser && message.content.includes("```")) ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              a: ({ node, href, children, ...restProps }) => {
                const isCitationLink = href && /^\d+$/.test(href);
                if (isCitationLink) {
                  const citationNumber = parseInt(href, 10);
                  const index = citationNumber - 1;
                  const contextForTooltip =
                    citationContexts &&
                    index >= 0 &&
                    index < citationContexts.length
                      ? citationContexts[index]
                      : null;

                  const { style } =
                    restProps as React.HTMLAttributes<HTMLElement>;

                  return (
                    <TooltipProvider delayDuration={100}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            style={style}
                            className={`text-blue-600 dark:text-blue-400 hover:underline focus:outline-none focus:ring-1 focus:ring-blue-500 rounded-sm px-0.5 py-0 align-super text-xs ${
                              (restProps as any).className || ""
                            }`}
                            onClick={() => handleCitationClick(citationNumber)}
                            aria-label={`View details for citation ${citationNumber}`}
                            type="button"
                          >
                            <sup>[{citationNumber}]</sup>
                          </button>
                        </TooltipTrigger>
                        {contextForTooltip && (
                          <TooltipContent className="max-w-xs bg-background text-foreground border shadow-lg rounded-md p-2">
                            <p className="text-xs font-medium">
                              Source:{" "}
                              {contextForTooltip.metadata.file_name || "N/A"}
                            </p>
                            {contextForTooltip.metadata.headers &&
                              Object.keys(contextForTooltip.metadata.headers)
                                .length > 0 && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  {Object.values(
                                    contextForTooltip.metadata.headers,
                                  ).join(" > ")}
                                </p>
                              )}
                            <p className="text-xs mt-1 line-clamp-3">
                              {contextForTooltip.page_content}
                            </p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>
                  );
                }
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    {...restProps}
                  >
                    {children}
                  </a>
                );
              },
            }}
          >
            {markdownParseWithCitations(message.content)}
          </ReactMarkdown>
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}

        {(isLiveStreaming || message.isStreaming) && (
          <div className="flex items-center space-x-1 pt-1 text-xs text-muted-foreground">
            <FiLoader className="w-3 h-3 animate-spin" />
            <span>Streaming...</span>
          </div>
        )}
        <div
          className="text-xs mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2"
          title={
            message.created_at
              ? new Date(message.created_at).toLocaleString()
              : "Sending..."
          }
        >
          <span
            className={
              isUser ? "text-primary-foreground/70" : "text-muted-foreground"
            }
          >
            ID: {displayId}
          </span>
          {!isUser && !message.tempId && message.id !== 0 && (
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 p-0"
              onClick={() =>
                copyToClipboard(message.content, message.id.toString())
              }
            >
              {copiedId === message.id.toString() ? (
                <FiCheck className="h-3 w-3" />
              ) : (
                <FiCopy className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    );

    return (
      <div
        key={messageKey}
        className={`flex items-end space-x-2 group mb-2 ${
          isUser ? "justify-end" : "justify-start"
        }`}
      >
        {!isUser && avatar}
        {messageContent}
        {isUser && avatar}
      </div>
    );
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
    return (
      <div className="p-4 text-center">
        Chat session not found or could not be loaded.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] relative bg-muted/20">
      <header className="p-4 border-b bg-background shadow-sm">
        <h1
          className="text-xl font-semibold truncate"
          title={chatSession.title}
        >
          {chatSession.title}
        </h1>
      </header>
      <main className="flex-1 overflow-y-auto p-4 space-y-1 pb-[100px]">
        {messages.map((msg) => renderMessage(msg, false))}
        {streamingAssistantMessage &&
          renderMessage(streamingAssistantMessage, true)}
        <div ref={messagesEndRef} />
      </main>
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
            if (e.key === "Enter" && !e.shiftKey && !isLoadingStream) {
              handleSubmit(e);
            }
          }}
        />
        <Button
          type="submit"
          disabled={isLoadingStream || isFetchingHistory || !input.trim()}
          className="h-10 px-4 py-2"
          aria-label="Send message"
        >
          {isLoadingStream ? (
            <FiLoader className="h-4 w-4 animate-spin" />
          ) : (
            <FiSend className="h-4 w-4" />
          )}
        </Button>
      </form>

      <Dialog
        open={isCitationDialogOpen}
        onOpenChange={setIsCitationDialogOpen}
      >
        <DialogContent className="sm:max-w-[625px] bg-background text-foreground border shadow-xl">
          <DialogHeader>
            <DialogTitle>
              Citation:{" "}
              {selectedCitation?.metadata.file_name || "Source Details"}
            </DialogTitle>
            {selectedCitation?.metadata.chunk_id && (
              <DialogDescription className="text-xs">
                Document ID: {selectedCitation.metadata.document_id || "N/A"} |
                Chunk ID: {selectedCitation.metadata.chunk_id}
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="prose prose-sm dark:prose-invert max-w-none max-h-[60vh] overflow-y-auto py-4 px-1 pretty-scrollbar">
            {selectedCitation ? (
              <>
                {selectedCitation.metadata.headers &&
                  Object.keys(selectedCitation.metadata.headers).length > 0 && (
                    <div className="mb-3 p-2 border-l-2 border-primary bg-muted/50 rounded-r-md">
                      <p className="text-xs font-semibold text-primary">
                        In section:{" "}
                        {Object.values(selectedCitation.metadata.headers).join(
                          " / ",
                        )}
                      </p>
                    </div>
                  )}
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                >
                  {selectedCitation.page_content}
                </ReactMarkdown>
              </>
            ) : (
              <p>No citation details available.</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
