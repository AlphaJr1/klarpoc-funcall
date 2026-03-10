import { useState, useRef, useCallback } from "react";
import type { ChatHistory, ChatPhase, ChatClarifyOpts } from "../types";

export function useChat() {
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatHistory>([]);
  const [chatPhase, setChatPhase] = useState<ChatPhase>("idle");
  const [chatClarify, setChatClarify] = useState<ChatClarifyOpts | null>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  const addUserMessage = useCallback((content: string) => {
    setChatHistory(prev => [...prev, { role: "user", content }]);
    setChatInput("");
    setChatClarify(null);
  }, []);

  const addAssistantMessage = useCallback((content: string) => {
    setChatHistory(prev => [...prev, { role: "assistant", content }]);
  }, []);

  const resetChat = useCallback(() => {
    setChatHistory([]);
    setChatInput("");
    setChatClarify(null);
    setChatPhase("idle");
  }, []);

  const focusInput = useCallback(() => {
    setTimeout(() => chatInputRef.current?.focus(), 100);
  }, []);

  return {
    chatInput,
    setChatInput,
    chatHistory,
    setChatHistory,
    chatPhase,
    setChatPhase,
    chatClarify,
    setChatClarify,
    chatInputRef,
    addUserMessage,
    addAssistantMessage,
    resetChat,
    focusInput,
  };
}
