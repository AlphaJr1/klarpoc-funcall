import { useCallback } from "react";
import type { Task, StreamStep } from "../types";

interface UseTaskResetDeps {
  setIsResetting: React.Dispatch<React.SetStateAction<boolean>>;
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  setSelectedTask: React.Dispatch<React.SetStateAction<Task | null>>;
  setActiveTaskDetail: React.Dispatch<React.SetStateAction<Task | null>>;
  setStreamingSteps: React.Dispatch<React.SetStateAction<StreamStep[]>>;
}

export function useTaskReset({
  setIsResetting,
  setTasks,
  setSelectedTask,
  setActiveTaskDetail,
  setStreamingSteps,
}: UseTaskResetDeps) {
  return useCallback(async () => {
    if (!confirm("Reset semua task ke status open? ai_response & trace akan dihapus.")) return;
    setIsResetting(true);
    try {
      await fetch("/api-backend/tasks/reset", { method: "POST" });
      const res = await fetch("/api-backend/tasks");
      const d = await res.json();
      if (d.tasks) setTasks(d.tasks);
      setSelectedTask(null);
      setActiveTaskDetail(null);
      setStreamingSteps([]);
    } catch {}
    setIsResetting(false);
  }, [
    setIsResetting,
    setTasks,
    setSelectedTask,
    setActiveTaskDetail,
    setStreamingSteps,
  ]);
}
