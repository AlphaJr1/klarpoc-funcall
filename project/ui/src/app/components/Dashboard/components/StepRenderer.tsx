import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { StreamStep } from "../types";
import { markdownComponents } from "./markdown";
import {
  ThinkingStep,
  ToolCallStep,
  ConfidenceStep,
  PostProgressStep,
  ShadowCheckStep,
  ClarifyReplyStep,
  Gate0ClarifyStep
} from "../processing";
import {
  Database, Sparkles, Loader2, AlertCircle, Bot, RefreshCw
} from "lucide-react";
import { buildToolCallResultMap } from "../utils/streamHelpers";

interface StepRendererProps {
  steps: StreamStep[];
  availableBrands: string[];
  isProcessing: boolean;
  onRegenerate: () => void;
  onClarifyAnswer: (answer: string) => void;
}

export default function StepRenderer({
  steps,
  availableBrands,
  isProcessing,
  onRegenerate,
  onClarifyAnswer
}: StepRendererProps) {
  if (steps.length === 0) return null;

  const toolCallResultMap = buildToolCallResultMap(steps);
  const shadowCheckStep = steps.find(s => s.event === "shadow_check") as (StreamStep & { event: "shadow_check" }) | undefined;
  const doneStep = steps.find(s => s.event === "done") as (StreamStep & { event: "done" }) | undefined;

  const rendered: React.ReactNode[] = [];
  let toolCallIdx = 0;

  steps.forEach((step, i) => {
    if (step.event === "thinking") {
      if (step.stage === "inner_monologue") return;
      if (step.stage === "reasoning") {
        const hasToolCallAfter = steps.slice(i + 1).some(s => s.event === "tool_call");
        const isDone = !!doneStep;
        if (isDone && !hasToolCallAfter) return;
      }
      rendered.push(
        <div key={i} className="animate-in fade-in slide-in-from-bottom-1 duration-300">
          <ThinkingStep step={step} />
        </div>
      );
    } else if (step.event === "tool_call") {
      const resultStep = toolCallResultMap.get(toolCallIdx++);
      rendered.push(
        <div key={i} className="animate-in fade-in slide-in-from-bottom-1 duration-300">
          <ToolCallStep step={step} result={resultStep} />
        </div>
      );
    } else if (step.event === "tool_result") {
      // skip
    } else if (step.event === "confidence") {
      const explStep = steps.find(s => s.event === "confidence_explanation") as (StreamStep & { event: "confidence_explanation" }) | undefined;
      rendered.push(
        <div key={i} className="animate-in fade-in slide-in-from-bottom-1 duration-300">
          <ConfidenceStep step={step} explanations={explStep?.explanations} />
        </div>
      );
    } else if (step.event === "confidence_explanation") {
      // skip: merged into ConfidenceStep
    } else if (step.event === "post_progress") {
      // collected and rendered later as one block, skip here
    } else if (step.event === "shadow_check" || step.event === "done") {
      // defer to later for order: confidence -> shadow_check -> done
    } else if (step.event === "cached") {
      const cachedStep = step as StreamStep & { event: "cached" };
      rendered.push(
        <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-violet-500/30 bg-violet-500/5 text-xs text-violet-300 animate-in fade-in duration-300">
          <Database className="w-3.5 h-3.5 shrink-0" />
          <span className="font-medium">Cache Hit</span>
          <span className="opacity-70">{cachedStep.message}</span>
          <span className="ml-auto px-1.5 py-0.5 rounded bg-violet-500/20 text-[10px] font-mono uppercase">cached</span>
        </div>
      );
    } else if (step.event === "clarification_needed") {
      // Inject brand options if slot empty
      const enrichedStep = {
        ...step,
        slots: step.slots.map(slot => ({
          ...slot,
          options: slot.options?.length > 0
            ? slot.options
            : (slot.label?.toLowerCase().includes("brand") ? availableBrands : slot.options ?? [])
        }))
      };
      // If no slots at all, add Brand slot
      if (!enrichedStep.slots.length) {
        enrichedStep.slots = [{ label: "Brand", options: availableBrands }];
      }
      rendered.push(
        <ClarifyReplyStep
          key={i}
          step={enrichedStep}
          onSubmit={(answer) => onClarifyAnswer(answer)}
        />
      );
    } else if (step.event === "gate0_clarify") {
      rendered.push(
        <div key={i} className="animate-in fade-in slide-in-from-bottom-2 duration-400">
          <Gate0ClarifyStep
            step={step}
            onSubmit={(answer) => onClarifyAnswer(answer)}
          />
        </div>
      );
    } else if (step.event === "query_refined") {
      const refinedStep = step as StreamStep & { event: "query_refined" };
      rendered.push(
        <div key={i} className="animate-in fade-in slide-in-from-bottom-1 duration-300 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-3 py-2.5 text-xs space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-indigo-400">✨ Query Refined</p>
          <div className="space-y-1">
            <div className="flex gap-1.5">
              <span className="text-gray-500 w-24 shrink-0">Original</span>
              <span className="text-gray-400 line-through opacity-60">{refinedStep.original}</span>
            </div>
            <div className="flex gap-1.5">
              <span className="text-gray-500 w-24 shrink-0">Klarifikasi</span>
              <span className="text-amber-300/80">{refinedStep.clarification}</span>
            </div>
            <div className="flex gap-1.5">
              <span className="text-gray-500 w-24 shrink-0">Refined</span>
              <span className="text-indigo-200 font-medium">{refinedStep.refined}</span>
            </div>
          </div>
        </div>
      );
    } else if (step.event === "error") {
      const errorStep = step as StreamStep & { event: "error" };
      rendered.push(
        <div key={i} className="p-3 rounded-lg border border-red-500/30 bg-red-500/5 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {errorStep.message}
        </div>
      );
    }
  });

  // Render post_progress (retry indicator) before draft/final answer
  const progressSteps = steps.filter(s => s.event === "post_progress") as (StreamStep & { event: "post_progress" })[];
  if (progressSteps.length > 0 && !shadowCheckStep) {
    rendered.push(
      <div key="post-progress" className="animate-in fade-in duration-300">
        <PostProgressStep steps={progressSteps} />
      </div>
    );
  }

  // Render done (Draft Answer) — after natural position, but before shadow_check if any
  if (doneStep && !shadowCheckStep) {
    // Shadow check not yet → Draft Answer
    rendered.push(
      <div key="done-draft" className="animate-in fade-in slide-in-from-bottom-2 duration-500 mt-2">
        <div className="rounded-xl border border-gray-600/40 bg-gray-800/30 overflow-hidden shadow-lg">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-700/50 bg-gray-700/20">
            <Sparkles className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-xs font-semibold text-gray-500 flex items-center gap-1.5">
              <Loader2 className="w-3 h-3 animate-spin" />
              Draft Answer
              <span className="text-[10px] font-normal text-gray-600 ml-1">— menunggu shadow check...</span>
            </span>
          </div>
          <div className="p-4 text-sm text-gray-500">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{doneStep.response}</ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  // Render shadow_check step
  if (shadowCheckStep) {
    rendered.push(
      <div key="shadow-check-final" className="animate-in fade-in slide-in-from-bottom-1 duration-300">
        <ShadowCheckStep step={shadowCheckStep} />
      </div>
    );
  }

  // Render final answer (done + shadow_check)
  if (doneStep && shadowCheckStep) {
    const shadowFlagged = shadowCheckStep.result === "FLAG";
    const effectiveResolution = shadowFlagged
      ? "AM Review Required (Shadow Check FLAG)"
      : doneStep.resolution;
    const isAMReview = shadowFlagged || effectiveResolution.includes("Review");

    rendered.push(
      <div key="done-final" className="animate-in fade-in slide-in-from-bottom-2 duration-500 mt-2">
        <div className={`rounded-xl border overflow-hidden shadow-lg ${
          isAMReview
            ? "border-amber-500/30 bg-gray-900/50"
            : "border-indigo-500/20 bg-gray-900/50"
        }`}>
          <div className={`flex items-center gap-2 px-4 py-2.5 border-b ${
            isAMReview
              ? "border-amber-800/40 bg-amber-500/5"
              : "border-gray-800/80 bg-indigo-500/5"
          }`}>
            <Sparkles className={`w-3.5 h-3.5 ${isAMReview ? "text-amber-400" : "text-indigo-400"}`} />
            <span className={`text-xs font-semibold ${isAMReview ? "text-amber-300" : "text-indigo-300"}`}>Final Answer</span>
            {doneStep.cached && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 font-mono">cached</span>
            )}
            <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-bold ${
              isAMReview
                ? "bg-amber-500/25 text-amber-200 border border-amber-500/40"
                : "bg-emerald-500/20 text-emerald-300"
            }`}>{effectiveResolution}</span>
          </div>
          <div className="p-4 text-sm text-gray-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{doneStep.response}</ReactMarkdown>
          </div>
          {isAMReview && !doneStep.cached && (
            <div className="mx-4 mb-4 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 flex items-center gap-2 text-xs">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" /> Escalation task dibuat untuk review AM
            </div>
          )}
          <div className="px-4 py-3 bg-gray-900/40 border-t border-gray-800 flex justify-end">
            <button
              onClick={onRegenerate}
              disabled={isProcessing}
              title="Regenerate — proses ulang dari AI"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 disabled:opacity-40 text-xs font-medium transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? "animate-spin" : ""}`} />
              Regenerate Response
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="flex-1 space-y-2">
        {rendered}
        {isProcessing && (
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping delay-100" />
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping delay-200" />
          </div>
        )}
      </div>
    </div>
  );
}
