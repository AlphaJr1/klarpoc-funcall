"use client";

import React from "react";
import { STAGE_ICONS, STAGE_LABEL } from "../constants";
import type { StreamStep } from "../types";

interface ThinkingStepProps {
  step: StreamStep & { event: "thinking" };
}

export default function ThinkingStep({ step }: ThinkingStepProps) {
  const colors: Record<string, string> = {
    understanding: "border-violet-500/30 bg-violet-500/5 text-violet-300",
    reasoning: "border-sky-500/30 bg-sky-500/5 text-sky-300",
    inner_monologue: "border-amber-500/30 bg-amber-500/5 text-amber-300",
  };

  const context = step.context || {};

  return (
    <div className={`rounded-lg border px-3 py-2.5 text-xs leading-relaxed ${colors[step.stage]}`}>
      <div className="flex items-center gap-1.5 font-medium mb-1 opacity-70">
        {STAGE_ICONS[step.stage]}
        {STAGE_LABEL[step.stage]}
      </div>
      <p className="opacity-90 font-mono">{step.message}</p>
      {context && Object.keys(context).length > 0 && (
        <div className="mt-2 space-y-1.5">
          {/* State badge + confidence */}
          {context.state && (
            <div className="flex flex-col gap-1.5 mb-2 bg-violet-500/10 p-2 rounded-md border border-violet-500/20">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded-full bg-violet-600/30 text-violet-200 font-bold text-[10px] uppercase tracking-wide">
                  🔀 {String(context.state)}
                </span>
                {context.state_desc && (
                  <span className="text-[11px] text-violet-300 font-medium">
                    {String(context.state_desc)}
                  </span>
                )}
                {context.state_confidence && (
                  <span className="text-[10px] text-gray-400 font-mono ml-auto">
                    confidence: <span className="text-emerald-400 font-bold">{String(context.state_confidence)}</span>
                  </span>
                )}
              </div>
              {context.state_reasoning && (
                <div className="text-[10px] text-gray-400 italic">
                  &quot;{String(context.state_reasoning)}&quot;
                </div>
              )}
            </div>
          )}
          {/* Allowed tools pills */}
          {context.allowed_tools && Array.isArray(context.allowed_tools) && (
            <div className="flex flex-wrap gap-1">
              <span className="text-[10px] text-gray-500 mr-0.5">tools:</span>
              {(context.allowed_tools as string[]).map(t => (
                <span key={t} className="px-1.5 py-0.5 rounded bg-sky-500/15 border border-sky-500/20 text-sky-300 font-mono text-[10px]">{t}</span>
              ))}
            </div>
          )}
          {/* Other context keys */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(context)
              .filter(([k]) => !['state','state_confidence','state_reasoning','allowed_tools'].includes(k))
              .map(([k, v]) => (
                <span key={k} className="px-1.5 py-0.5 rounded bg-white/5 font-mono text-[10px]">
                  {k}: <span className="opacity-80">{String(v)}</span>
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
