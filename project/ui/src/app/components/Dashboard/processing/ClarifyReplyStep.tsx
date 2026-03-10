"use client";

import React, { useState } from "react";
import { AlertCircle, ChevronRight, CheckCircle2 } from "lucide-react";
import type { StreamStep } from "../types";

interface ClarifyReplyStepProps {
  step: StreamStep & { event: "clarification_needed" };
  onSubmit: (answer: string) => void;
}

export default function ClarifyReplyStep({ step, onSubmit }: ClarifyReplyStepProps) {
  // State per slot: index -> selected value (""|"__other__"|string)
  const [selections, setSelections] = useState<Record<number, string>>({});
  const [others, setOthers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const setSlot = (i: number, val: string) =>
    setSelections(p => ({ ...p, [i]: val }));
  const setOther = (i: number, val: string) =>
    setOthers(p => ({ ...p, [i]: val }));

  const allFilled = step.slots.every((_, i) => {
    const sel = selections[i];
    return !!sel && (sel !== "__other__" || !!others[i]?.trim());
  });

  const handleSubmit = () => {
    if (!allFilled) return;
    const answers = step.slots.map((slot, i) => {
      const sel = selections[i];
      const val = sel === "__other__" ? others[i].trim() : sel;
      return `${slot.label}: ${val}`;
    });
    setSubmitted(true);
    onSubmit(answers.join(" | "));
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-1 duration-300 rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 space-y-4">
      <div className="flex items-center gap-2 font-semibold text-amber-400 text-xs">
        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
        Klarifikasi Diperlukan
      </div>

      <p className="text-sm text-gray-200">{step.question}</p>

      {!submitted && (
        <div className="space-y-4">
          {step.slots.map((slot, i) => (
            <div key={i} className="space-y-2">
              <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">{slot.label}</p>
              <div className="flex flex-wrap gap-2">
                {(slot.options ?? []).map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setSlot(i, opt)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 ${
                      selections[i] === opt
                        ? "border-amber-400 bg-amber-500/30 text-amber-200"
                        : "border-gray-600 bg-gray-800/60 text-gray-300 hover:border-amber-500/50 hover:bg-amber-500/10"
                    }`}
                  >
                    {selections[i] === opt && <span className="mr-1.5">✓</span>}
                    {opt}
                  </button>
                ))}
                <button
                  onClick={() => setSlot(i, "__other__")}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 ${
                    selections[i] === "__other__"
                      ? "border-amber-400 bg-amber-500/20 text-amber-200"
                      : "border-dashed border-gray-600 bg-transparent text-gray-400 hover:border-amber-500/50 hover:text-amber-300"
                  }`}
                >
                  ✏️ Other
                </button>
              </div>
              {selections[i] === "__other__" && (
                <input
                  autoFocus
                  type="text"
                  value={others[i] ?? ""}
                  onChange={e => setOther(i, e.target.value)}
                  placeholder={`Ketik ${(slot.label ?? "").toLowerCase()} secara manual...`}
                  className="w-full bg-gray-800/80 border border-amber-500/30 rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-400 transition-colors"
                />
              )}
            </div>
          ))}

          <button
            onClick={handleSubmit}
            disabled={!allFilled}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium text-white transition-colors"
          >
            <span>Konfirmasi & Proses</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      )}
      {submitted && (
        <div className="flex items-center gap-2 text-xs text-emerald-400 pt-1 border-t border-amber-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Memproses ulang dengan konteks yang dipilih...</span>
        </div>
      )}
    </div>
  );
}
