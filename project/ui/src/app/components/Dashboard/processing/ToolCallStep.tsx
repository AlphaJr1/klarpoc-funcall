"use client";

import React, { useState } from "react";
import { Wrench, ChevronUp, ChevronDown, Loader2 } from "lucide-react";
import type { StreamStep } from "../types";

interface ToolCallStepProps {
  step: StreamStep & { event: "tool_call" };
  result?: StreamStep & { event: "tool_result" };
}

export default function ToolCallStep({ step, result }: ToolCallStepProps) {
  const [open, setOpen] = useState(false);
  const dataSource = result?.result?._data_source as string | undefined;

  return (
    <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-xs font-mono text-blue-300 hover:bg-blue-500/10 transition-colors"
      >
        <Wrench className="w-3.5 h-3.5 shrink-0" />
        <span className="flex-1 text-left line-clamp-1">
          <span className="opacity-60 mr-1">call</span>
          <span className="font-semibold">{step.tool}</span>
          <span className="opacity-50 ml-1 text-[10px]">({Object.keys(step.input).join(", ")})</span>
        </span>
        {dataSource && (
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase whitespace-nowrap ${
               dataSource.includes('API') ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
            }`}>
              {dataSource.includes('API') ? '🟢 Live API' : '🟡 Dummy'}
            </span>
        )}
        {result ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 whitespace-nowrap">✓ done</span>
        ) : (
          <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
        )}
        {open ? <ChevronUp className="w-3 h-3 opacity-50 shrink-0" /> : <ChevronDown className="w-3 h-3 opacity-50 shrink-0" />}
      </button>
      {open && (
        <div className="border-t border-blue-500/20 text-[11px] font-mono">
          <div className="px-3 py-2 bg-black/30">
            <p className="text-gray-500 mb-1">INPUT</p>
            <pre className="text-blue-200 whitespace-pre-wrap">{JSON.stringify(step.input, null, 2)}</pre>
          </div>
          {result && (
            <div className="px-3 py-2 bg-black/20 border-t border-blue-500/10">
              <p className="text-gray-500 mb-1">RESULT</p>
              <pre className="text-emerald-200 whitespace-pre-wrap overflow-auto max-h-48">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
