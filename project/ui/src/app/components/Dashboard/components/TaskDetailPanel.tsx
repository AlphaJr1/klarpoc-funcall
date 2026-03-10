import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  CheckCircle2, Pencil, RefreshCw, AlertCircle, Bot, PhoneCall, Loader2
} from "lucide-react";

import type { Task } from "../types";
import { markdownComponents } from "./markdown";

interface TaskDetailPanelProps {
  activeTaskDetail: Task | null;
  isProcessing: boolean;
  isSubmittingToClickUp: boolean;
  submitSuccess: string | null;
  onEditResponse: () => void;
  onRegenerate: (task: Task) => void;
  onSubmitToClickUp: () => void;
}

export default function TaskDetailPanel({
  activeTaskDetail,
  isProcessing,
  isSubmittingToClickUp,
  submitSuccess,
  onEditResponse,
  onRegenerate,
  onSubmitToClickUp
}: TaskDetailPanelProps) {
  if (!activeTaskDetail) {
    return (
      <div className="w-[28%] min-w-[280px] flex flex-col bg-gray-900/50 h-full overflow-hidden">
        <div className="p-5 border-b border-gray-800/80 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
            <CheckCircle2 className="w-5 h-5 text-indigo-400" /> Task Detail
          </h2>
        </div>
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-3">
            <PhoneCall className="w-10 h-10 opacity-20" />
            <p className="text-sm">No task completed yet</p>
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "resolved":
        return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
      case "complete":
        return "bg-teal-500/20 text-teal-400 border border-teal-500/30";
      case "in_progress":
        return "bg-blue-500/20 text-blue-400 border border-blue-500/30";
      case "in_review":
        return "bg-amber-500/20 text-amber-400 border border-amber-500/30";
      default:
        return "bg-red-500/20 text-red-400 border border-red-500/30";
    }
  };

  const isAMReview = activeTaskDetail.status === "escalated";

  return (
    <div className="w-[28%] min-w-[280px] flex flex-col bg-gray-900/50 h-full overflow-hidden">
      <div className="p-5 border-b border-gray-800/80 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
          <CheckCircle2 className="w-5 h-5 text-indigo-400" /> Task Detail
        </h2>
      </div>
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="p-5 flex flex-col gap-4 shrink-0">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className={`inline-flex items-center px-2 py-1 rounded text-[10px] font-bold uppercase ${getStatusBadgeClass(activeTaskDetail.status)}`}>
                {activeTaskDetail.status}
              </span>
              <div className="flex items-center gap-1.5">
                {activeTaskDetail.ai_response && activeTaskDetail.status !== "complete" && (
                  <button
                    onClick={onEditResponse}
                    disabled={isProcessing}
                    title="Edit AI Response"
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 disabled:opacity-40 text-[11px] font-medium transition-colors"
                  >
                    <Pencil className="w-3 h-3" />
                    Edit Response
                  </button>
                )}
                <button
                  onClick={() => onRegenerate(activeTaskDetail)}
                  disabled={isProcessing}
                  title="Regenerate — proses ulang dari AI"
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 disabled:opacity-40 text-[11px] font-medium transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 ${isProcessing ? "animate-spin" : ""}`} />
                  Regenerate
                </button>
              </div>
            </div>
            <h3 className="text-sm font-medium text-gray-200">{activeTaskDetail.task_name}</h3>
          </div>
        </div>

        {/* AI Response — grows to fill space */}
        <div className="flex-1 flex flex-col min-h-0 px-5 gap-2 overflow-hidden">
          <h4 className="text-xs font-semibold uppercase text-gray-500 flex items-center gap-1 shrink-0">
            <Bot className="w-3 h-3" /> AI Response
          </h4>
          <div className="flex-1 overflow-y-auto p-4 rounded-xl bg-gray-900/60 border border-gray-700/50 text-sm text-gray-300 shadow-inner">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {activeTaskDetail.ai_response || "No response recorded."}
            </ReactMarkdown>
          </div>
        </div>

        {/* Bottom sticky section */}
        <div className="px-5 pb-4 shrink-0 flex flex-col gap-3">
          {(activeTaskDetail.comments?.length ?? 0) > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase text-gray-500">Agent Summary</h4>
              {activeTaskDetail.comments?.map((c, i: number) => (
                <div key={i} className="p-3 rounded-lg border border-indigo-500/20 bg-indigo-500/5 text-xs text-gray-300 max-h-32 overflow-auto">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{c.text}</ReactMarkdown>
                </div>
              ))}
            </div>
          )}

          {isAMReview && (
            <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10">
              <h4 className="text-xs font-semibold text-red-400 flex items-center gap-1 mb-1">
                <AlertCircle className="w-3 h-3" /> Escalated Task
              </h4>
              <p className="text-xs text-red-300/80">Pending human verification via AM.</p>
            </div>
          )}

          {activeTaskDetail.ai_response && activeTaskDetail.status !== "complete" && (
            <div className="pt-2 border-t border-gray-800">
              {submitSuccess === activeTaskDetail.task_id ? (
                <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-medium">
                  <CheckCircle2 className="w-4 h-4" />
                  Berhasil disubmit ke ClickUp — status: complete
                </div>
              ) : (
                <button
                  id="btn-submit-clickup"
                  onClick={onSubmitToClickUp}
                  disabled={isSubmittingToClickUp || isProcessing}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold text-white transition-all duration-200 shadow-lg shadow-indigo-500/20"
                >
                  {isSubmittingToClickUp ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Submitting...</>
                  ) : (
                    <><CheckCircle2 className="w-4 h-4" /> Submit to ClickUp</>
                  )}
                </button>
              )}
              <p className="text-[10px] text-gray-600 text-center mt-1.5">
                AM approve → status: complete, summary → ClickUp description
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
