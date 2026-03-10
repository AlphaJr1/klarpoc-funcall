"use client";

import React from "react";
import { Plus, X, Pencil } from "lucide-react";
import DateRangePicker from "../../DateRangePicker";

interface TaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  formData: {
    task_name: string;
    brand: string;
    date_range: string;
    priority: string;
    description: string;
  };
  onFormDataChange: (data: {
    task_name: string;
    brand: string;
    date_range: string;
    priority: string;
    description: string;
  }) => void;
  formError: string;
  isSubmitting: boolean;
  mode: "create" | "edit";
}

export default function TaskFormModal({
  isOpen,
  onClose,
  onSubmit,
  formData,
  onFormDataChange,
  formError,
  isSubmitting,
  mode,
}: TaskFormModalProps) {
  if (!isOpen) return null;

  const handleChange = (field: keyof typeof formData, value: string) => {
    onFormDataChange({ ...formData, [field]: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md mx-4 shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <h3 className="font-semibold text-white flex items-center gap-2">
            {mode === "create" ? (
              <>
                <Plus className="w-4 h-4 text-indigo-400" /> New Task
              </>
            ) : (
              <>
                <Pencil className="w-4 h-4 text-amber-400" /> Edit Task
              </>
            )}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Query / Question <span className="text-red-400">*</span>
            </label>
            <textarea
              rows={3}
              placeholder="e.g. What was total revenue for Brand A last week?"
              value={formData.task_name}
              onChange={(e) => handleChange("task_name", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">
                Brand <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.brand}
                onChange={(e) => handleChange("brand", e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="Kopi_Brand_A">Kopi_Brand_A</option>
                <option value="Fashion_Brand_B">Fashion_Brand_B</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => handleChange("priority", e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              >
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Date Range <span className="text-red-400">*</span>
            </label>
            <DateRangePicker
              value={formData.date_range}
              onChange={(val) => handleChange("date_range", val)}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Description <span className="text-gray-600">(opsional)</span>
            </label>
            <input
              type="text"
              placeholder="Additional context..."
              value={formData.description}
              onChange={(e) => handleChange("description", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          {formError && <p className="text-xs text-red-400">{formError}</p>}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-700 text-sm text-gray-300 hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-sm font-medium text-white transition-colors"
            >
              {isSubmitting
                ? mode === "create"
                  ? "Creating..."
                  : "Saving..."
                : mode === "create"
                ? "Create Task"
                : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
