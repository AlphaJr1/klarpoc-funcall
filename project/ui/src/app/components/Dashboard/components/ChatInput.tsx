import React, { forwardRef } from "react";
import { ChevronRight, X, Loader2 } from "lucide-react";
import type { ChatClarifyOpts, ChatPhase } from "../types";

interface ChatInputProps {
  chatClarify: ChatClarifyOpts | null;
  chatPhase: ChatPhase;
  chatInput: string;
  onChatInputChange: (value: string) => void;
  chatInputRef: React.RefObject<HTMLTextAreaElement | null>;
  onSubmit: (value?: string) => void;
  chatHistoryLength: number;
  onReset: () => void;
}

export default forwardRef<HTMLDivElement, ChatInputProps>(function ChatInput(
  {
    chatClarify,
    chatPhase,
    chatInput,
    onChatInputChange,
    chatInputRef,
    onSubmit,
    chatHistoryLength,
    onReset
  },
  ref
) {
  return (
    <div ref={ref} className="shrink-0 border-t border-gray-800/80 bg-gray-950/90 backdrop-blur p-4">
      {/* Clarification options */}
      {chatClarify && chatPhase === "clarify" && (
        <div className="mb-3 space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {Object.entries(chatClarify.options).map(([field, opts]) => (
            <div key={field} className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{field}</p>
              <div className="flex flex-wrap gap-1.5">
                {(opts as string[]).map((opt) => (
                  <button
                    key={opt}
                    onClick={() => onSubmit(opt)}
                    className="px-3 py-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium hover:bg-indigo-500/25 hover:border-indigo-400/50 transition-all duration-150"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-3 w-full max-w-2xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            ref={chatInputRef}
            rows={1}
            value={chatInput}
            onChange={e => {
              onChatInputChange(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
            }}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSubmit();
              }
            }}
            disabled={chatPhase === "thinking" || chatPhase === "creating"}
            placeholder={chatPhase === "clarify" ? "Atau ketik jawaban manual..." : "Tanya apa saja... (mis: revenue Kopi Brand A minggu lalu)"}
            className="w-full bg-gray-800/80 border border-gray-700/60 rounded-xl px-4 py-3 pr-12 text-sm text-gray-200 placeholder-gray-500/80 focus:outline-none focus:border-indigo-500/60 focus:bg-gray-800 resize-none transition-all duration-200 leading-relaxed disabled:opacity-50"
            style={{ minHeight: "46px", maxHeight: "160px", overflow: "auto" }}
          />
          {(chatPhase === "thinking" || chatPhase === "creating") && (
            <div className="absolute right-3 bottom-3">
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
            </div>
          )}
        </div>
        <button
          onClick={() => onSubmit()}
          disabled={!chatInput.trim() || chatPhase === "thinking" || chatPhase === "creating"}
          className="shrink-0 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 shadow-lg shadow-indigo-500/20"
        >
          <ChevronRight className="w-4 h-4 text-white" />
        </button>
        {chatHistoryLength > 0 && chatPhase === "idle" && (
          <button
            onClick={onReset}
            title="Reset chat"
            className="shrink-0 w-10 h-10 rounded-xl border border-gray-700 hover:bg-gray-800 text-gray-500 hover:text-gray-300 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      {chatHistoryLength === 0 && (
        <p className="text-center text-[10px] text-gray-600 mt-2">AI akan mengklarifikasi info yang kurang sebelum membuat task</p>
      )}
    </div>
  );
});
