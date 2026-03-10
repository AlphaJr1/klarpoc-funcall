"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import type { StreamStep } from "../types";

interface PostProgressStepProps {
  steps: (StreamStep & { event: "post_progress" })[];
}

export default function PostProgressStep({ steps }: PostProgressStepProps) {
  // Group by task, store latest attempt
  const byTask: Record<string, { attempt: number; max: number }> = {};
  for (const s of steps) {
    if (!byTask[s.task] || s.attempt > byTask[s.task].attempt) {
      byTask[s.task] = { attempt: s.attempt, max: s.max };
    }
  }

  const taskLabels: Record<string, string> = {
    shadow_check: "🛡️ Shadow Check",
    ai_reasoning: "🧠 AI Reasoning",
  };

  return (
    <div className="flex flex-col gap-1.5">
      {Object.entries(byTask).map(([task, { attempt, max }]) => (
        <div
          key={task}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-violet-500/20 bg-violet-500/5 text-xs text-violet-300"
        >
          <Loader2 className="w-3 h-3 animate-spin shrink-0" />
          <span className="font-medium">{taskLabels[task] ?? task}</span>
          <span className="text-gray-500">— mencoba</span>
          <span className="tabular-nums font-bold text-violet-200">{attempt}/{max}</span>
          <span className="text-gray-500">kali...</span>
        </div>
      ))}
    </div>
  );
}
