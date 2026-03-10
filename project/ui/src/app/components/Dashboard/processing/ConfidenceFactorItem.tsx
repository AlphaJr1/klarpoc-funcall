"use client";

import React, { useState } from "react";
import { Brain, ChevronUp, ChevronDown } from "lucide-react";
import { FACTOR_META, factorBarColor, factorTextColor } from "../constants";

interface ConfidenceFactorItemProps {
  factorKey: string;
  val: { score: number; weight: string; reason: string };
  contribution: number;
  explanation?: string;
}

export default function ConfidenceFactorItem({
  factorKey,
  val,
  contribution,
  explanation
}: ConfidenceFactorItemProps) {
  const meta = FACTOR_META[factorKey] || { icon: "•", label: factorKey };
  const [insightOpen, setInsightOpen] = useState(true);

  return (
    <div className="space-y-1 mt-3">
      <div className="flex items-center gap-2">
        <span className="text-sm">{meta.icon}</span>
        <span className="font-semibold text-gray-200 flex-1 text-sm">{meta.label}</span>
        <span className="text-xs text-gray-500">{val.weight}</span>
        <span className={`text-sm font-bold tabular-nums ml-1 ${factorTextColor(val.score)}`}>
          {val.score}%
        </span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${factorBarColor(val.score)}`}
            style={{ width: `${val.score}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 tabular-nums w-12 text-right">+{contribution}pts</span>
      </div>
      <p className="text-xs text-gray-400 leading-relaxed pl-0.5 mt-1">{val.reason}</p>

      {explanation && (
        <div className="mt-2 rounded-md border border-violet-500/20 bg-violet-500/5 overflow-hidden">
          <button
            onClick={() => setInsightOpen(!insightOpen)}
            className="w-full flex items-center justify-between px-3 py-2 hover:bg-violet-500/10 transition-colors"
          >
            <div className="flex items-center gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wide text-violet-300 bg-violet-500/20 px-1.5 py-0.5 rounded flex items-center gap-1.5">
                <Brain className="w-3.5 h-3.5" /> AI Insight
              </span>
            </div>
            {insightOpen ? <ChevronUp className="w-3.5 h-3.5 text-violet-400/70" /> : <ChevronDown className="w-3.5 h-3.5 text-violet-400/70" />}
          </button>

          {insightOpen && (
            <div className="px-3 pb-3 pt-1 border-t border-violet-500/10">
              <p className="text-[13px] text-violet-200/90 leading-relaxed">{explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
