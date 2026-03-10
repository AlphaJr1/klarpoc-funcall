import React from "react";
import { Brain, CircleDot, Sparkles } from "lucide-react";

// Stage icons for thinking steps
export const STAGE_ICONS: Record<string, React.ReactNode> = {
  understanding: <Brain className="w-3.5 h-3.5" />,
  reasoning: <CircleDot className="w-3.5 h-3.5" />,
  inner_monologue: <Sparkles className="w-3.5 h-3.5" />,
};

// Stage labels for display
export const STAGE_LABEL: Record<string, string> = {
  understanding: "Memahami Prompt",
  reasoning: "Berpikir...",
  inner_monologue: "Inner Monologue",
};

// Factor metadata for confidence breakdown
export const FACTOR_META: Record<string, { icon: string; label: string }> = {
  completeness:    { icon: "✅", label: "Completeness" },
  tool_routing:    { icon: "🔀", label: "Tool Routing" },
  complexity:      { icon: "🧩", label: "Complexity" },
  data_validation: { icon: "🔍", label: "Data Validation" },
  freshness:       { icon: "⏱️", label: "Freshness" },
  dnc:             { icon: "🧠", label: "DNC (Reasoning)" },
};

// Priority order for sorting
export const PRIORITY_ORDER: Record<string, number> = {
  "Urgent": 0,
  "High": 1,
  "Medium": 2,
  "Low": 3,
};

// Helper function to get bar color based on score
export function factorBarColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

// Helper function to get text color based on score
export function factorTextColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 50) return "text-amber-400";
  return "text-red-400";
}

// Helper function to get badge class based on score
export function scoreBadgeClass(score: number): string {
  if (score >= 80) return "bg/20 text-em-emerald-500erald-300 border-emerald-500/30";
  if (score >= 50) return "bg-amber-500/20 text-amber-300 border-amber-500/30";
  return "bg-red-500/20 text-red-300 border-red-500/30";
}

// Default brands available in the system
export const DEFAULT_BRANDS = [
  "Kopi_Brand_A",
  "Fashion_Brand_B",
  "Restoran_Brand_C",
  "Klar_Lixus_PoC",
];
