"use client";

import React, { useState } from "react";
import { TrendingUp, ChevronUp, ChevronDown } from "lucide-react";
import { scoreBadgeClass } from "../constants";
import ConfidenceFactorItem from "./ConfidenceFactorItem";
import type { StreamStep } from "../types";

interface ConfidenceStepProps {
  step: StreamStep & { event: "confidence" };
  explanations?: Record<string, string>;
}

export default function ConfidenceStep({ step, explanations }: ConfidenceStepProps) {
  const [expanded, setExpanded] = useState(true);
  const isHigh = step.score >= 80;
  const isMed = step.score >= 50;
  const ringColor = isHigh
    ? "border-emerald-500/40 bg-emerald-500/5"
    : isMed ? "border-amber-500/40 bg-amber-500/5"
    : "border-red-500/40 bg-red-500/5";
  const mainTextColor = isHigh ? "text-emerald-400" : isMed ? "text-amber-400" : "text-red-400";
  const mainBarColor = isHigh ? "bg-emerald-500" : isMed ? "bg-amber-500" : "bg-red-500";
  const interpretation = isHigh
    ? "Jawaban dapat dikirim langsung ke customer"
    : isMed ? "Perlu review AM sebelum dikirim"
    : "Perlu eskalasi ke specialist";
  const breakdown = step.breakdown || {};

  return (
    <div className={`rounded-lg border text-xs overflow-hidden ${ringColor}`}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-2 px-3 py-2.5 hover:bg-white/5 transition-colors"
      >
        <TrendingUp className="w-3.5 h-3.5 shrink-0" style={{ color: isHigh ? "#34d399" : isMed ? "#fbbf24" : "#f87171" }} />
        <span className={`font-bold text-sm ${mainTextColor}`}>{step.score}%</span>
        <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold border ${scoreBadgeClass(step.score)}`}>
          {step.label}
        </span>
        <span className="text-gray-500 text-[10px] ml-1">— {interpretation}</span>
        <span className="ml-auto text-gray-600">
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </span>
      </button>

      <div className="px-3 pb-2">
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-1000 ${mainBarColor}`} style={{ width: `${step.score}%` }} />
        </div>
      </div>

      {expanded && (
        <div className="px-3 py-3 space-y-4 border-t border-white/5">
          <div className="text-[11px] text-gray-500 font-mono bg-black/20 rounded px-3 py-2 leading-relaxed">
            Score = completeness×25% + tool_routing×20% + complexity×15% + data_validation×15% + freshness×15% + dnc×10%
          </div>
          <div className="space-y-5 divide-y divide-white/5">
            {Object.entries(breakdown).map(([key, val]) => {
              const contribution = Math.round(val.score * parseFloat(val.weight) / 100);
              return (
                <div key={key} className="pt-2 first:pt-0">
                  <ConfidenceFactorItem
                    factorKey={key}
                    val={val}
                    contribution={contribution}
                    explanation={explanations?.[key]}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
