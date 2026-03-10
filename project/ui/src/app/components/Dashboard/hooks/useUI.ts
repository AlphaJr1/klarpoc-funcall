import { useState } from "react";

export function useUI() {
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showEditResponseModal, setShowEditResponseModal] = useState(false);
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [isSubmittingToClickUp, setIsSubmittingToClickUp] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  return {
    showModal,
    setShowModal,
    showEditModal,
    setShowEditModal,
    showEditResponseModal,
    setShowEditResponseModal,
    isLeftPanelOpen,
    setIsLeftPanelOpen,
    isRightPanelOpen,
    setIsRightPanelOpen,
    isResetting,
    setIsResetting,
    isSubmittingToClickUp,
    setIsSubmittingToClickUp,
    submitSuccess,
    setSubmitSuccess,
  };
}
