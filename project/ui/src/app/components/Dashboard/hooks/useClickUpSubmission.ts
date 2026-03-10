import { useCallback } from "react";
import type { Task } from "../types";

interface UseClickUpSubmissionDeps {
  activeTaskDetail: Task | null;
  setIsSubmittingToClickUp: React.Dispatch<React.SetStateAction<boolean>>;
  setSubmitSuccess: React.Dispatch<React.SetStateAction<string | null>>;
  setActiveTaskDetail: React.Dispatch<React.SetStateAction<Task | null>>;
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
}

export function useClickUpSubmission({
  activeTaskDetail,
  setIsSubmittingToClickUp,
  setSubmitSuccess,
  setActiveTaskDetail,
  setTasks,
}: UseClickUpSubmissionDeps) {
  return useCallback(async () => {
    if (!activeTaskDetail) return;
    const summary = activeTaskDetail.ai_response || "";
    if (!summary) return;
    setIsSubmittingToClickUp(true);
    setSubmitSuccess(null);
    try {
      const res = await fetch(`/api-backend/tasks/${activeTaskDetail.task_id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ai_summary: summary }),
      });
      if (!res.ok) throw new Error();
      await res.json();
      setSubmitSuccess(activeTaskDetail.task_id);
      setActiveTaskDetail((prev) => prev ? { ...prev, status: "complete" } : null);
      setTasks(prev => prev.map(t =>
        t.task_id === activeTaskDetail.task_id ? { ...t, status: "complete" } : t
      ));
    } catch {
      alert("Gagal submit ke ClickUp.");
    } finally {
      setIsSubmittingToClickUp(false);
    }
  }, [
    activeTaskDetail,
    setIsSubmittingToClickUp,
    setSubmitSuccess,
    setActiveTaskDetail,
    setTasks,
  ]);
}
