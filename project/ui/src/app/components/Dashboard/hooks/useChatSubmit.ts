import { useState, useCallback, useRef } from "react";
import type { Task, ChatHistory, ChatPhase, ChatClarifyOpts } from "../types";

interface UseChatSubmitOptions {
  onCreateTask?: (task: Task) => void;
  onStartProcessing?: (task: Task, force?: boolean, queryOverride?: string) => void;
  selectedTask?: Task | null;
  activeTaskDetail?: Task | null;
}

export function useChatSubmit(options: UseChatSubmitOptions = {}) {
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatHistory>([]);
  const [chatPhase, setChatPhase] = useState<ChatPhase>("idle");
  const [chatClarify, setChatClarify] = useState<ChatClarifyOpts | null>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  const handleChatSubmit = useCallback(async (messageOverride?: string) => {
    const msg = (messageOverride ?? chatInput).trim();
    if (!msg || chatPhase === "thinking" || chatPhase === "creating") return;

    if (options.selectedTask) {
      const activeResponse = options.activeTaskDetail?.ai_response || options.selectedTask.ai_response || "";
      const queryOverride = `Konteks Sebelumnya:\nPertanyaan awal: ${options.selectedTask.task_name}\nJawaban AI sebelumnya: ${activeResponse}\n\nPertanyaan lanjutan user: ${msg}\nHarap jawab pertanyaan lanjutan ini dengan tetap mengacu pada konteks sebelumnya.`;

      setChatHistory(prev => [...prev, { role: "user", content: msg }]);
      setChatInput("");
      setChatClarify(null);

      options.onStartProcessing?.(options.selectedTask, true, queryOverride);
      return;
    }

    const newHistory: ChatHistory = [...chatHistory, { role: "user", content: msg }];
    setChatHistory(newHistory);
    setChatInput("");
    setChatClarify(null);
    setChatPhase("thinking");

    try {
      const res = await fetch("/api-backend/tasks/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: chatHistory }),
      });
      const data = await res.json();

      if (data.status === "ready" && data.task) {
        setChatPhase("creating");
        const newTask = data.task;
        setChatHistory(prev => [
          ...prev,
          { role: "assistant", content: `✅ Task dibuat: **${newTask.task_name}** (${newTask.custom_fields?.Brand}, ${newTask.custom_fields?.["Date Range"]})` }
        ]);
        options.onCreateTask?.(newTask);
        setTimeout(() => {
          setChatPhase("done");
          options.onStartProcessing?.(newTask, true);
          setTimeout(() => {
            setChatHistory([]);
            setChatPhase("idle");
          }, 2000);
        }, 500);
      } else if (data.status === "clarify") {
        setChatPhase("clarify");
        setChatClarify({
          message: data.message || data.assistant_message || "Mohon lengkapi info berikut:",
          missing_fields: data.missing_fields || [],
          options: data.options || {},
        });
        setChatHistory(prev => [
          ...prev,
          { role: "assistant", content: data.message || data.assistant_message || "Mohon lengkapi info berikut:" }
        ]);
      } else {
        setChatPhase("idle");
        setChatHistory(prev => [
          ...prev,
          { role: "assistant", content: data.message || "Terjadi kesalahan, coba lagi." }
        ]);
      }
    } catch {
      setChatPhase("idle");
      setChatHistory(prev => [...prev, { role: "assistant", content: "Gagal terhubung ke server." }]);
    }
  }, [chatInput, chatPhase, chatHistory, options]);

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
    handleChatSubmit,
    resetChat,
    focusInput,
  };
}
