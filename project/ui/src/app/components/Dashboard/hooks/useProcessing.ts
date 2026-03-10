import { useState, useEffect, useRef, useCallback } from "react";
import type { Task, StreamStep, ChatHistory } from "../types";

interface UseProcessingOptions {
  onTaskUpdate?: (updater: (prev: Task[]) => Task[]) => void;
  onActiveTaskDetailUpdate?: (task: Task | null) => void;
  onTasksUpdate?: (tasks: Task[]) => void;
  onSelectedTaskUpdate?: (task: Task | null | ((prev: Task | null) => Task | null)) => void;
  onChatHistoryUpdate?: (history: ChatHistory | ((prev: ChatHistory) => ChatHistory)) => void;
}

export function useProcessing(options: UseProcessingOptions = {}) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamingSteps, setStreamingSteps] = useState<StreamStep[]>([]);
  const [processingMs, setProcessingMs] = useState(0);
  const [totalMs, setTotalMs] = useState<number | null>(null);
  
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const t0Ref = useRef<number>(0);
  const lastEventMsRef = useRef<number>(0);

  const startTimer = useCallback(() => {
    setProcessingMs(0);
    setTotalMs(null);
    t0Ref.current = performance.now();
    timerRef.current = setInterval(() => {
      setProcessingMs(Math.round(performance.now() - t0Ref.current));
    }, 100);
  }, []);

  const stopTimer = useCallback((finalMs?: number) => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setTotalMs(finalMs ?? Math.round(performance.now() - t0Ref.current));
    setProcessingMs(0);
  }, []);

  const uiLog = useCallback((taskId: string, event: string, detail = "") => {
    const elapsed = Math.round(performance.now() - t0Ref.current);
    const delta = elapsed - lastEventMsRef.current;
    lastEventMsRef.current = elapsed;
    fetch("/api-backend/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId, event, elapsed_ms: elapsed, delta_ms: delta, detail }),
    }).catch(() => {});
  }, []);

  const fetchTaskDetails = useCallback(async (id: string, overrides: { response?: string; summary?: string }) => {
    const summary = overrides.summary || "";
    try {
      const res = await fetch(`/api-backend/tasks/${id}`);
      const data = await res.json();
      const updatedTask = {
        ...overrides,
        ...data?.task,
        ai_response: overrides.response,
        comments: summary ? [{ author: "AI Agent", text: summary }] : [],
      };
      options.onActiveTaskDetailUpdate?.(updatedTask);
    } catch {
      // Error handling in caller
    }
  }, [options]);

  const runMockStreaming = useCallback((task: Task) => {
    const mockSteps: StreamStep[] = [
      { event: "thinking", stage: "understanding", message: `Memahami pertanyaan: "${task.task_name}"`, context: { brand: "Kopi_Brand_A", store_id: "store_001", date_range: task.custom_fields?.["Date Range"] || "" } },
      { event: "thinking", stage: "reasoning", message: "[Iterasi 1] Menentukan tool yang tepat..." },
      { event: "tool_call", tool: "get_date_range_metrics", input: { store_id: "store_001", start_date: "2026-01-01", end_date: "2026-01-31" } },
      { event: "tool_result", tool: "get_date_range_metrics", result: { total_revenue: 15420000, total_transactions: 312, avg_order_value: 49423 } },
      { event: "thinking", stage: "reasoning", message: "[Iterasi 2] Menganalisis hasil dan menyusun jawaban..." },
      { event: "thinking", stage: "inner_monologue", message: "Data revenue sudah diperoleh. Perlu membandingkan antar periode." },
      { event: "tool_call", tool: "get_date_range_metrics", input: { store_id: "store_001", start_date: "2026-02-01", end_date: "2026-02-27" } },
      { event: "tool_result", tool: "get_date_range_metrics", result: { total_revenue: 11830000, total_transactions: 241, avg_order_value: 49086 } },
      { event: "confidence", score: 72, label: "medium", breakdown: { completeness: { score: 100, weight: "25%", reason: "Semua 2 tool call berhasil" }, tool_routing: { score: 100, weight: "20%", reason: "2 tool unik dipanggil tanpa redundansi" }, complexity: { score: 70, weight: "15%", reason: "3 keyword terdeteksi — query cukup jelas" }, data_validation: { score: 100, weight: "15%", reason: "Tidak ada anomali terdeteksi dalam data" }, freshness: { score: 10, weight: "15%", reason: "Data 30+ hari yang lalu — historical" }, dnc: { score: 100, weight: "10%", reason: "Reasoning trace konsisten, tidak ada konflik" } } },
      { event: "done", resolution: "AM Review Required", response: "**Revenue Comparison Jan vs Feb 2026**\n\n| Periode | Revenue | Transaksi |\n|---|---|---|\n| Jan 2026 | Rp 15.420.000 | 312 |\n| Feb 2026 | Rp 11.830.000 | 241 |\n\nRevenue Feb 2026 turun **23.3%** dibanding Jan 2026." },
    ];

    let delay = 0;
    mockSteps.forEach(step => {
      const d = step.event === "tool_result" ? delay += 600 : delay += 800;
      setTimeout(() => {
        setStreamingSteps(prev => [...prev, step]);
        if (step.event === "done") {
          setIsProcessing(false);
          options.onActiveTaskDetailUpdate?.({
            ...task,
            status: "in_review",
            ai_response: step.response,
            comments: [{ author: "AI Agent", text: "🤖 Mock summary: AI berhasil memproses task menggunakan 2 tool calls." }],
          });
        }
      }, d);
    });
  }, [options]);

  const startProcessing = useCallback(async (task: Task, force = false, queryOverride?: string) => {
    if (isProcessing) return;
    
    options.onSelectedTaskUpdate?.(task);
    if (!queryOverride) {
      options.onChatHistoryUpdate?.(task.chat_history || []);
    }
    setStreamingSteps([]);
    setTotalMs(null);
    setProcessingMs(0);

    // Cache replay
    if (!force && !queryOverride && task.ai_response) {
      options.onActiveTaskDetailUpdate?.(task);
      setIsProcessing(false);
      fetch(`/api-backend/tasks/${task.task_id}/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) })
        .then(async resp => {
          const reader = resp.body?.getReader();
          const decoder = new TextDecoder();
          if (!reader) return;
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            for (const line of chunk.split("\n")) {
              if (line.startsWith("data: ")) {
                try { setStreamingSteps(prev => [...prev, JSON.parse(line.substring(6)) as StreamStep]); } catch { /* ignore parse errors */ }
              }
            }
          }
        })
        .catch(() => {});
      return;
    }

    options.onActiveTaskDetailUpdate?.(null);
    setIsProcessing(true);
    startTimer();
    lastEventMsRef.current = 0;
    uiLog(task.task_id, "START_PROCESSING", `task="${task.task_name.slice(0, 60)}"`);

    const url = `/api-backend/tasks/${task.task_id}/run${force ? "?force=true" : ""}`;
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_override: queryOverride ?? null }),
      });
      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          for (const line of chunk.split("\n")) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6)) as StreamStep;
                setStreamingSteps(prev => [...prev, data]);

                const detail = (() => {
                  if (data.event === "thinking") return `stage=${data.stage}`;
                  if (data.event === "tool_call") return `tool=${data.tool}`;
                  if (data.event === "tool_result") return `tool=${data.tool}`;
                  if (data.event === "confidence") return `score=${data.score}%`;
                  if (data.event === "done") return `*** ANSWER VISIBLE *** timing_ms=${data.timing_ms}`;
                  if (data.event === "shadow_check") return `result=${data.result}`;
                  if (data.event === "gate0") return `result=${data.result}`;
                  if (data.event === "confidence_explanation") return `keys=${Object.keys(data.explanations ?? {}).join(",")}`;
                  return "";
                })();
                uiLog(task.task_id, data.event, detail);

                if (data.event === "done") {
                  const backendMs = data.timing_ms;
                  stopTimer(backendMs);
                  setIsProcessing(false);

                  if (queryOverride) {
                    options.onChatHistoryUpdate?.(prev => [...prev, { role: "assistant", content: data.response }]);
                    fetch(`/api-backend/tasks/${task.task_id}/chat_history`, {
                      method: "PATCH",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ chat_history: [...(task.chat_history || []), { role: "assistant", content: data.response }] }),
                    }).catch(() => {});
                    task.chat_history = [...(task.chat_history || []), { role: "assistant", content: data.response }];
                  }

                  options.onTaskUpdate?.(prev => prev.map(t =>
                    t.task_id === task.task_id
                      ? { ...t, ai_response: data.response, chat_history: task.chat_history }
                      : t
                  ));
                  fetchTaskDetails(task.task_id, data);
                } else if (data.event === "gate0_clarify" || data.event === "clarification_needed" || data.event === "error") {
                  stopTimer();
                  setIsProcessing(false);
                } else if (data.event === "query_refined") {
                  const refinedCmd = data as StreamStep & { event: "query_refined" };
                  options.onSelectedTaskUpdate?.(prev => prev && prev.task_id === task.task_id ? { ...prev, task_name: refinedCmd.refined } : prev);
                  options.onTaskUpdate?.(prev => prev.map(t => t.task_id === task.task_id ? { ...t, task_name: refinedCmd.refined } : t));
                  task.task_name = refinedCmd.refined;
                  fetch(`/api-backend/tasks/${task.task_id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name: refinedCmd.refined }),
                  }).catch(() => {});
                }
              } catch { /* ignore parse errors */ }
            }
          }
        }
      }
    } catch {
      runMockStreaming(task);
    }
  }, [isProcessing, startTimer, stopTimer, uiLog, fetchTaskDetails, runMockStreaming, options]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return {
    isProcessing,
    setIsProcessing,
    streamingSteps,
    setStreamingSteps,
    processingMs,
    setProcessingMs,
    totalMs,
    setTotalMs,
    startTimer,
    stopTimer,
    uiLog,
    fetchTaskDetails,
    runMockStreaming,
    startProcessing,
    lastEventMsRef,
    t0Ref,
  };
}
