import { useState, useCallback } from "react";
import type { Task } from "../types";

export function useEditResponse() {
  const [showModal, setShowModal] = useState(false);
  const [editResponseData, setEditResponseData] = useState("");

  const handleOpenEditResponse = useCallback((task: Task) => {
    setEditResponseData(task.ai_response || "");
    setShowModal(true);
  }, []);

  const handleSaveEditResponse = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!editResponseData) return;
    setShowModal(false);
  }, [editResponseData]);

  const closeModal = useCallback(() => {
    setShowModal(false);
  }, []);

  return {
    showModal,
    setShowModal,
    editResponseData,
    setEditResponseData,
    handleOpenEditResponse,
    handleSaveEditResponse,
    closeModal,
  };
}
