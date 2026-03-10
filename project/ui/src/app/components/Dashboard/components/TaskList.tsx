import React from "react";
import { Pencil, Search, Clock, Activity, RefreshCw, Plus } from "lucide-react";
import { PRIORITY_ORDER } from "../constants";
import type { Task } from "../types";

interface TaskListProps {
  tasks: Task[];
  selectedTask: Task | null;
  isProcessing: boolean;
  isResetting: boolean;
  onSelectTask: (task: Task) => void;
  onEditTask: (task: Task) => void;
  onResetAll: () => void;
  onNewTask: () => void;
}

export default function TaskList({
  tasks,
  selectedTask,
  isProcessing,
  isResetting,
  onSelectTask,
  onEditTask,
  onResetAll,
  onNewTask,
}: TaskListProps) {
  return (
    <div className="w-[28%] min-w-[280px] border-r border-gray-800 flex flex-col bg-gray-900/50 h-full overflow-hidden">
      <div className="p-5 border-b border-gray-800/80 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
            <Activity className="w-5 h-5 text-indigo-400" /> Task Queue
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={onResetAll}
              disabled={isResetting || isProcessing}
              title="Reset semua task ke open"
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20 disabled:opacity-40 text-xs font-medium transition-colors"
            >
              <RefreshCw className={`w-3 h-3 ${isResetting ? "animate-spin" : ""}`} />
              Reset
            </button>
            <button onClick={onNewTask}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-colors">
              <Plus className="w-3.5 h-3.5" /> New Task
            </button>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {[...tasks].sort((a, b) => {
          return (PRIORITY_ORDER[a.custom_fields?.Priority || "Low"] ?? 4) - (PRIORITY_ORDER[b.custom_fields?.Priority || "Low"] ?? 4);
        }).map(t => (
          <div key={t.task_id} onClick={() => onSelectTask(t)}
            className={`w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
              selectedTask?.task_id === t.task_id
                ? "bg-indigo-900/20 border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.1)]"
                : "bg-gray-800/40 border-gray-700/50 hover:bg-gray-800 hover:border-gray-600"
            } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-mono text-gray-400">{t.task_id}</span>
              <div className="flex items-center gap-1.5">
                <button onClick={(e) => { e.stopPropagation(); onEditTask(t); }} className="p-1 rounded text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"><Pencil className="w-3.5 h-3.5" /></button>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                  t.custom_fields?.Priority === "Urgent" ? "bg-rose-600/25 text-rose-300 border-rose-500/50 shadow-[0_0_8px_rgba(225,29,72,0.3)]" :
                  t.custom_fields?.Priority === "High"   ? "bg-orange-500/20 text-orange-300 border-orange-500/40" :
                  t.custom_fields?.Priority === "Medium" ? "bg-amber-400/15 text-amber-300 border-amber-400/30" :
                  "bg-blue-500/15 text-blue-300 border-blue-500/25"
                }`}>{t.custom_fields?.Priority}</span>
              </div>
            </div>
            <p className="font-medium text-sm text-gray-200 leading-snug">{t.task_name}</p>
            <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                t.status === "open" ? "bg-sky-500/15 text-sky-400" :
                t.status === "in_progress" ? "bg-blue-500/15 text-blue-400" :
                t.status === "resolved" ? "bg-emerald-500/15 text-emerald-400" :
                t.status === "complete" ? "bg-teal-500/15 text-teal-400" :
                t.status === "escalated" ? "bg-red-500/15 text-red-400" : "bg-amber-500/15 text-amber-400"
              }`}>{t.status}</span>
              <span className="flex items-center gap-1"><Search className="w-3 h-3" />{t.custom_fields?.Brand}</span>
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{t.custom_fields?.["Date Range"] || "N/A"}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
