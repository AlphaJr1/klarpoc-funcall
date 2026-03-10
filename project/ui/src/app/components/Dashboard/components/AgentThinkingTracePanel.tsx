import React, { useEffect, useRef } from "react";
import { ThreadPrimitive } from "@assistant-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot, PanelLeft, PanelRight, Loader2, CheckCircle2
} from "lucide-react";

import type { StreamStep, Task, ChatHistory, ChatPhase, ChatClarifyOpts } from "../types";
import { markdownComponents } from "./markdown";
import StepRenderer from "./StepRenderer";
import ChatInput from "./ChatInput";

interface AgentThinkingTracePanelProps {
  // Toggle states
  isLeftPanelOpen: boolean;
  setIsLeftPanelOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isRightPanelOpen: boolean;
  setIsRightPanelOpen: React.Dispatch<React.SetStateAction<boolean>>;
  // Processing
  isProcessing: boolean;
  processingMs: number;
  totalMs: number | null;
  // Task and streaming
  selectedTask: Task | null;
  streamingSteps: StreamStep[];
  startProcessing: (task: Task, reset?: boolean, clarification?: string) => void;
  // Chat
  chatHistory: ChatHistory;
  chatPhase: ChatPhase;
  chatClarify: ChatClarifyOpts | null;
  setChatClarify: React.Dispatch<React.SetStateAction<ChatClarifyOpts | null>>;
  chatInput: string;
  setChatInput: React.Dispatch<React.SetStateAction<string>>;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatHistory>>;
  chatInputRef: React.RefObject<HTMLTextAreaElement | null>;
  handleChatSubmit: (value?: string) => void;
  // Brands for clarification
  availableBrands: string[];
}

export default function AgentThinkingTracePanel({
  isLeftPanelOpen,
  setIsLeftPanelOpen,
  isRightPanelOpen,
  setIsRightPanelOpen,
  isProcessing,
  processingMs,
  totalMs,
  selectedTask,
  streamingSteps,
  startProcessing,
  chatHistory,
  chatPhase,
  chatClarify,
  setChatClarify,
  setChatHistory,
  chatInput,
  setChatInput,
  chatInputRef,
  handleChatSubmit,
  availableBrands,
}: AgentThinkingTracePanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamingSteps]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, chatPhase]);

  return (
    <div className="flex-1 flex flex-col bg-gray-950 relative border-r border-gray-800 h-full overflow-hidden min-w-[320px]">
      {/* Header */}
      <div className="p-5 border-b border-gray-800/80 bg-gray-900/80 backdrop-blur sticky top-0 z-10 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsLeftPanelOpen(!isLeftPanelOpen)}
            title="Toggle Task Queue"
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 bg-gray-900 border border-gray-700 transition-colors"
          >
            <PanelLeft className="w-4 h-4" />
          </button>
          <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
            <Bot className="w-5 h-5 text-indigo-400" /> Agent Thinking Trace
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {isProcessing ? (
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Processing...</span>
              <span className="tabular-nums text-emerald-300/70">{(processingMs / 1000).toFixed(1)}s</span>
            </div>
          ) : totalMs !== null ? (
            <div className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Selesai dalam</span>
              <span className="tabular-nums font-bold text-emerald-400">{(totalMs / 1000).toFixed(1)}s</span>
            </div>
          ) : null}
          <button
            onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
            title="Toggle Task Detail"
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 bg-gray-900 border border-gray-700 transition-colors"
          >
            <PanelRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5">
        {/* Placeholder */}
        {!selectedTask && chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-3">
            <Bot className="w-10 h-10 opacity-30" />
            <p className="text-sm">Ketik pertanyaan di bawah untuk membuat task baru</p>
          </div>
        ) : selectedTask ? (
          <ThreadPrimitive.Root className="w-full max-w-2xl mx-auto space-y-2">
            {/* User msg */}
            <div className="flex gap-3 mb-4">
              <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">U</div>
              <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl rounded-tl-none px-4 py-3 text-sm text-gray-200 flex-1 leading-relaxed">
                {selectedTask.task_name}
              </div>
            </div>

            {/* Follow-up user messages */}
            {chatHistory.length > 0 && (
              <div className="space-y-3 mb-4">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                    {msg.role === "assistant" && (
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed border ${
                      msg.role === "user"
                        ? "bg-indigo-600/80 text-white border-indigo-500/50 rounded-tr-none"
                        : "bg-gray-800/80 border-gray-700/50 text-gray-200 rounded-tl-none"
                    }`}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{msg.content}</ReactMarkdown>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">U</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Streaming steps */}
            {streamingSteps.length > 0 && (
              <StepRenderer
                steps={streamingSteps}
                availableBrands={availableBrands}
                isProcessing={isProcessing}
                onRegenerate={() => startProcessing(selectedTask, true)}
                onClarifyAnswer={(answer) => startProcessing(selectedTask, true, answer)}
              />
            )}

            <ThreadPrimitive.Messages components={{ Message: () => <></> }} />
          </ThreadPrimitive.Root>
        ) : null}

        {/* AI Chat messages when no selected task */}
        {!selectedTask && chatHistory.length > 0 && (
          <div className="w-full max-w-2xl mx-auto space-y-3 pb-4">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex gap-3 animate-in fade-in slide-in-from-bottom-1 duration-300 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-600/80 text-white rounded-tr-none"
                    : "bg-gray-800/80 border border-gray-700/50 text-gray-200 rounded-tl-none"
                }`}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{msg.content}</ReactMarkdown>
                </div>
                {msg.role === "user" && (
                  <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">U</div>
                )}
              </div>
            ))}
            {chatPhase === "thinking" && (
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shrink-0">
                  <Bot className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="bg-gray-800/80 border border-gray-700/50 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
            {chatPhase === "creating" && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm animate-in fade-in duration-300">
                <Loader2 className="w-4 h-4 animate-spin" />
                Membuat task dan menjalankan AI...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chat Input */}
      <ChatInput
        chatClarify={chatClarify}
        chatPhase={chatPhase}
        chatInput={chatInput}
        onChatInputChange={setChatInput}
        chatInputRef={chatInputRef}
        onSubmit={handleChatSubmit}
        chatHistoryLength={chatHistory.length}
        onReset={() => {
          setChatHistory([]);
          setChatClarify(null);
          setChatInput("");
        }}
      />
    </div>
  );
}
