"use client";

import React, { useState } from "react";
import { ChevronRight, CheckCircle2 } from "lucide-react";
import type { StreamStep } from "../types";

interface Gate0ClarifyStepProps {
  step: StreamStep & { event: "gate0_clarify" };
  onSubmit: (answer: string) => void;
}

export default function Gate0ClarifyStep({ step, onSubmit }: Gate0ClarifyStepProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [otherText, setOtherText] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    const answer = selected === "__other__" ? otherText.trim() : selected;
    if (!answer) return;
    setSubmitted(true);
    onSubmit(answer);
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 duration-400 rounded-xl border border-violet-500/30 bg-violet-500/5 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-base">🔍</span>
        <div>
          <p className="text-xs font-semibold text-violet-300">Gate 0 — Klarifikasi Diperlukan</p>
          <p className="text-[11px] text-gray-400 mt-0.5">{step.message}</p>
        </div>
      </div>

      {/* Question */}
      <p className="text-sm font-medium text-gray-200">{step.question}</p>

      {/* Option chips */}
      {!submitted && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {step.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => setSelected(opt)}
                className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 ${
                  selected === opt
                    ? "border-violet-400 bg-violet-500/30 text-violet-200"
                    : "border-gray-600 bg-gray-800/60 text-gray-300 hover:border-violet-500/50 hover:bg-violet-500/10"
                }`}
              >
                {selected === opt && <span className="mr-1.5">✓</span>}
                {opt}
              </button>
            ))}
            {/* Other option */}
            <button
              onClick={() => setSelected("__other__")}
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 ${
                selected === "__other__"
                  ? "border-amber-400 bg-amber-500/20 text-amber-200"
                  : "border-dashed border-gray-600 bg-transparent text-gray-400 hover:border-amber-500/50 hover:text-amber-300"
              }`}
            >
              ✏️ Other
            </button>
          </div>

          {/* Free-text jika pilih Other */}
          {selected === "__other__" && (
            <textarea
              autoFocus
              rows={2}
              value={otherText}
              onChange={e => setOtherText(e.target.value)}
              placeholder="Tulis klarifikasi kamu di sini..."
              className="w-full bg-gray-800/80 border border-amber-500/30 rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-400 resize-none transition-colors"
            />
          )}

          <button
            onClick={handleSubmit}
            disabled={!selected || (selected === "__other__" && !otherText.trim())}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium text-white transition-colors"
          >
            <span>Konfirmasi & Jalankan</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Submitted state */}
      {submitted && (
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Memproses ulang dengan klarifikasi...</span>
        </div>
      )}
    </div>
  );
}
