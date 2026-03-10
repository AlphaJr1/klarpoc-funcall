// StreamStep types - discriminated union for all event types in the streaming pipeline
export type StreamStep =
  | {
      event: "thinking";
      stage: "understanding" | "reasoning" | "inner_monologue";
      message: string;
      context?: Record<string, string | string[]>;
    }
  | { event: "tool_call"; tool: string; input: Record<string, unknown> }
  | { event: "tool_result"; tool: string; result: Record<string, unknown> }
  | {
      event: "confidence";
      score: number;
      label: string;
      breakdown: Record<
        string,
        { score: number; weight: string; reason: string }
      >;
    }
  | { event: "confidence_explanation"; explanations: Record<string, string> }
  | {
      event: "shadow_check";
      result: "PASS" | "FLAG";
      logic: string;
      disclosure: string;
      raw?: string;
    }
  | {
      event: "done";
      resolution: string;
      response: string;
      escalation_task?: unknown;
      summary?: string;
      cached?: boolean;
      timing_ms?: number;
    }
  | { event: "cached"; message: string }
  | { event: "gate0"; result: "VALID" | "CLARIFY"; message: string }
  | {
      event: "gate0_clarify";
      message: string;
      question: string;
      options: string[];
      note: string;
    }
  | {
      event: "query_refined";
      original: string;
      clarification: string;
      refined: string;
    }
  | {
      event: "clarification_needed";
      question: string;
      slots: { label: string; options: string[] }[];
      message: string;
    }
  | { event: "context_extracted"; brand: string; date_range: string }
  | {
      event: "post_progress";
      task: "shadow_check" | "ai_reasoning";
      attempt: number;
      max: number;
      status: "running";
    }
  | { event: "error"; message: string };

// Chat phases for the AI chat interface
export type ChatPhase = "idle" | "thinking" | "clarify" | "creating" | "done";

// Chat history message type
export type ChatHistory = { role: "user" | "assistant"; content: string }[];

// Chat clarification options
export type ChatClarifyOpts = {
  message: string;
  missing_fields: string[];
  options: Record<string, string[]>;
};

// Task type (from API)
export interface Task {
  task_id: string;
  task_name: string;
  status: string;
  description?: string;
  custom_fields?: {
    Brand?: string;
    "Date Range"?: string;
    Priority?: string;
  };
  ai_response?: string;
  chat_history?: ChatHistory;
  comments?: { author: string; text: string }[];
}

// Task form data for creating/editing tasks
export interface TaskFormData {
  task_name: string;
  brand: string;
  date_range: string;
  priority: string;
  description: string;
}

// Confidence breakdown item
export interface ConfidenceBreakdownItem {
  score: number;
  weight: string;
  reason: string;
}

// Factor meta information for confidence factors
export interface FactorMeta {
  icon: string;
  label: string;
}
