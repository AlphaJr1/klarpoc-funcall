import { useState, useCallback } from "react";
import type { Task } from "../types";

interface EditFormData {
  name: string;
  brand: string;
  date_range: string;
  priority: string;
  description: string;
}

export function useEditTask(
  onSuccess?: (task: Task) => void,
  availableBrands: string[] = []
) {
  const [showModal, setShowModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editFormData, setEditFormData] = useState<EditFormData>({
    name: "",
    brand: "",
    date_range: "",
    priority: "",
    description: "",
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editFormError, setEditFormError] = useState("");

  const handleOpenEdit = useCallback((task: Task) => {
    setEditingTask(task);
    setEditFormData({
      name: task.task_name || "",
      brand: task.custom_fields?.Brand || availableBrands[0] || "Kopi_Brand_A",
      date_range: task.custom_fields?.["Date Range"] || "",
      priority: task.custom_fields?.Priority || "Medium",
      description: task.description || "",
    });
    setShowModal(true);
  }, [availableBrands]);

  const handleEditTask = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTask) return;
    
    setEditFormError("");
    setIsEditing(true);
    try {
      const res = await fetch(`/api-backend/tasks/${editingTask.task_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editFormData),
      });
      if (!res.ok) throw new Error("Gagal edit task");
      const data = await res.json();
      onSuccess?.(data.task);
      setShowModal(false);
    } catch {
      setEditFormError("Gagal update task. Pastikan server aktif.");
    } finally {
      setIsEditing(false);
    }
  }, [editingTask, editFormData, onSuccess]);

  const closeModal = useCallback(() => {
    setShowModal(false);
    setEditFormError("");
  }, []);

  return {
    showModal,
    setShowModal,
    editingTask,
    setEditingTask,
    editFormData,
    setEditFormData,
    isEditing,
    setIsEditing,
    editFormError,
    setEditFormError,
    handleOpenEdit,
    handleEditTask,
    closeModal,
  };
}
