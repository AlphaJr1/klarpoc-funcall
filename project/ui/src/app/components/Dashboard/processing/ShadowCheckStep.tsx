"use client";

import React from "react";
import type { StreamStep } from "../types";

interface ShadowCheckStepProps {
  step: StreamStep & { event: "shadow_check" };
}

export default function ShadowCheckStep({ step }: ShadowCheckStepProps) {
  const isPass = step.result === "PASS";

  return (
    <div className={`rounded-lg border text-xs px-3 py-2.5 ${
      isPass
        ? "border-emerald-500/30 bg-emerald-500/5"
        : "border-red-500/50 bg-red-950/60 ring-1 ring-red-500/30"
    }`}>
      <div className={`flex items-center gap-2 font-bold mb-2.5 ${
        isPass ? "text-emerald-400" : "text-red-300"
      }`}>
        <span className="text-sm">{isPass ? "🛡️" : "🚨"}</span>
        Shadow Check
        <span className={`ml-auto px-2.5 py-0.5 rounded-full text-[10px] uppercase font-black border ${
          isPass
            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
            : "bg-red-500/30 text-red-200 border-red-400/60 shadow-[0_0_8px_rgba(239,68,68,0.4)]"
        }`}>{step.result}</span>
      </div>
      <div className="space-y-2">
        <div className="flex items-start gap-2">
          <span className="text-[10px] text-gray-500 w-20 shrink-0">Logic</span>
          <span className={`text-[10px] font-medium leading-relaxed ${
            step.logic.startsWith("PASS") ? "text-emerald-400" : "text-red-300"
          }`}>{step.logic}</span>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-[10px] text-gray-500 w-20 shrink-0">Disclosure</span>
          <span className={`text-[10px] font-medium leading-relaxed ${
            step.disclosure.startsWith("PASS") ? "text-emerald-400" : "text-red-300"
          }`}>{step.disclosure}</span>
        </div>
      </div>
      {!isPass && (
        <div className="mt-2.5 border-t border-red-500/30 pt-2.5 flex items-center gap-1.5">
          <span className="text-[10px] font-black text-red-400">⚡ BINARY VETO AKTIF</span>
          <span className="text-[10px] text-red-300/80">— jawaban WAJIB diarahkan ke AM Review, confidence score diabaikan</span>
        </div>
      )}
    </div>
  );
}
