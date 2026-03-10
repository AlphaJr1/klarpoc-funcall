import { useState, useEffect, useCallback } from "react";
import type { Task } from "../types";

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [activeTaskDetail, setActiveTaskDetail] = useState<Task | null>(null);
  const [availableBrands, setAvailableBrands] = useState<string[]>([]);

  useEffect(() => {
    fetch("/api-backend/tasks")
      .then(r => r.json())
      .then(d => { if (d.tasks) setTasks(d.tasks); })
      .catch(() => {
        setTasks([
          { task_id: "task_003", task_name: "Trend: Revenue comparison Jan 2026 vs Feb 2026", status: "escalated", custom_fields: { Brand: "Kopi_Brand_A", "Date Range": "Jan-Feb 2026", Priority: "High" } },
          { task_id: "task_006", task_name: "Customer retention: Repeat vs new customers, last 3 days", status: "in_review", custom_fields: { Brand: "Kopi_Brand_A", "Date Range": "Last 3 docs", Priority: "Medium" } },
          { task_id: "task_001", task_name: "What was total revenue yesterday (Feb 24)?", status: "resolved", custom_fields: { Brand: "Kopi_Brand_A", "Date Range": "Yesterday", Priority: "Low" } }
        ]);
      });
  }, []);

  useEffect(() => {
    fetch("/api-backend/brands")
      .then(r => r.json())
      .then(d => { if (d.brands?.length) setAvailableBrands(d.brands); })
      .catch(() => {});
  }, []);

  const handleResetAll = useCallback(async () => {
    if (!confirm("Reset semua task ke status open? ai_response & trace akan dihapus.")) return;
    try {
      await fetch("/api-backend/tasks/reset", { method: "POST" });
      const res = await fetch("/api-backend/tasks");
      const d = await res.json();
      if (d.tasks) setTasks(d.tasks);
      setSelectedTask(null);
      setActiveTaskDetail(null);
    } catch {}
  }, []);

  const updateTaskInList = useCallback((updatedTask: Task) => {
    setTasks(prev => prev.map(t => t.task_id === updatedTask.task_id ? updatedTask : t));
  }, []);

  const addTask = useCallback((newTask: Task) => {
    setTasks(prev => [newTask, ...prev]);
  }, []);

  return {
    tasks,
    setTasks,
    selectedTask,
    setSelectedTask,
    activeTaskDetail,
    setActiveTaskDetail,
    availableBrands,
    setAvailableBrands,
    handleResetAll,
    updateTaskInList,
    addTask,
  };
}
