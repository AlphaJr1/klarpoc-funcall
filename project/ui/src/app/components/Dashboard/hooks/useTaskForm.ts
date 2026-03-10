import { useState, useCallback } from "react";
import type { TaskFormData, Task } from "../types";
import { DEFAULT_BRANDS } from "../constants";

const DEFAULT_FORM_DATA: TaskFormData = {
  task_name: "",
  brand: DEFAULT_BRANDS[0] || "Kopi_Brand_A",
  date_range: "",
  priority: "Medium",
  description: "",
};

export function useTaskForm(onSuccess?: (task: Task) => void) {
  const [formData, setFormData] = useState<TaskFormData>(DEFAULT_FORM_DATA);
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = useCallback(() => {
    if (!formData.task_name.trim()) { setFormError("Query/Question wajib diisi."); return false; }
    if (!formData.brand) { setFormError("Brand wajib dipilih."); return false; }
    if (!formData.date_range.trim()) { setFormError("Date Range wajib diisi."); return false; }
    setFormError("");
    return true;
  }, [formData]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setIsSubmitting(true);
    try {
      const res = await fetch("/api-backend/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error("Gagal membuat task");
      const data = await res.json();
      onSuccess?.(data.task);
      setFormData(DEFAULT_FORM_DATA);
    } catch {
      setFormError("Gagal terhubung ke server.");
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validate, onSuccess]);

  const resetForm = useCallback(() => {
    setFormData(DEFAULT_FORM_DATA);
    setFormError("");
  }, []);

  return {
    formData,
    setFormData,
    formError,
    setFormError,
    isSubmitting,
    handleSubmit,
    resetForm,
    validate,
  };
}
