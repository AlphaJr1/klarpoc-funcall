"use client";

import { useLocalRuntime, AssistantRuntimeProvider } from "@assistant-ui/react";

// Import modals
import TaskFormModal from "./Dashboard/modals/TaskFormModal";
import EditResponseModal from "./Dashboard/modals/EditResponseModal";

// Import components
import TaskQueuePanel from "./Dashboard/components/TaskQueuePanel";

// Import custom hooks
import {
  useTasks,
  useTaskForm,
  useEditTask,
  useEditResponse,
  useProcessing,
  useChatSubmit,
  useUI,
  useTaskReset,
  useClickUpSubmission
} from "./Dashboard/hooks";

// Extracted panels
import AgentThinkingTracePanel from "./Dashboard/components/AgentThinkingTracePanel";
import TaskDetailPanel from "./Dashboard/components/TaskDetailPanel";

export default function Dashboard() {
  const {
    tasks,
    setTasks,
    selectedTask,
    setSelectedTask,
    activeTaskDetail,
    setActiveTaskDetail,
    availableBrands,
    updateTaskInList,
    addTask,
  } = useTasks();

  const {
    showModal: showCreateModal,
    setShowModal: setShowCreateModal,
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
  } = useUI();

  const {
    formData,
    setFormData,
    formError,
    setFormError,
    isSubmitting,
    handleSubmit: handleCreateTask,
  } = useTaskForm((newTask) => {
    addTask(newTask);
  });

  const {
    editFormData,
    setEditFormData,
    isEditing,
    editFormError,
    setEditFormError,
    handleOpenEdit,
    handleEditTask,
  } = useEditTask((updatedTask) => {
    updateTaskInList(updatedTask);
    if (activeTaskDetail?.task_id === updatedTask.task_id) setActiveTaskDetail(updatedTask);
    if (selectedTask?.task_id === updatedTask.task_id) setSelectedTask(updatedTask);
  }, availableBrands);

  const {
    editResponseData,
    setEditResponseData,
    handleSaveEditResponse,
  } = useEditResponse();

  const {
    isProcessing,
    streamingSteps,
    setStreamingSteps,
    processingMs,
    totalMs,
    startProcessing,
  } = useProcessing({
    onTaskUpdate: (updater) => setTasks(updater),
    onActiveTaskDetailUpdate: setActiveTaskDetail,
    onSelectedTaskUpdate: setSelectedTask,
  });

  const {
    chatInput,
    setChatInput,
    chatHistory,
    setChatHistory,
    chatPhase,
    chatClarify,
    setChatClarify,
    chatInputRef,
    handleChatSubmit,
  } = useChatSubmit({
    onCreateTask: (task) => setTasks(prev => [task, ...prev]),
    onStartProcessing: startProcessing,
    selectedTask,
    activeTaskDetail,
   });

  const runtime = useLocalRuntime({ run: async () => ({ content: [] }) });

  const resetAll = useTaskReset({
    setIsResetting,
    setTasks,
    setSelectedTask,
    setActiveTaskDetail,
    setStreamingSteps,
  });

  const submitToClickUp = useClickUpSubmission({
    activeTaskDetail,
    setIsSubmittingToClickUp,
    setSubmitSuccess,
    setActiveTaskDetail,
    setTasks,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex h-full w-full bg-gray-950 text-gray-100 overflow-hidden font-sans">

        {/* MODAL - Using extracted TaskFormModal component */}
        <TaskFormModal
          isOpen={showCreateModal}
          onClose={() => { setShowCreateModal(false); setFormError(""); }}
          onSubmit={handleCreateTask}
          formData={formData}
          onFormDataChange={setFormData}
          formError={formError}
          isSubmitting={isSubmitting}
          mode="create"
        />

        {/* EDIT MODAL - Using extracted TaskFormModal component */}
        <TaskFormModal
          isOpen={showEditModal}
          onClose={() => { setShowEditModal(false); setEditFormError(""); }}
          onSubmit={handleEditTask}
          formData={{
            task_name: editFormData.name,
            brand: editFormData.brand,
            date_range: editFormData.date_range,
            priority: editFormData.priority,
            description: editFormData.description
          }}
          onFormDataChange={(data) => setEditFormData({
            name: data.task_name,
            brand: data.brand,
            date_range: data.date_range,
            priority: data.priority,
            description: data.description
          })}
          formError={editFormError}
          isSubmitting={isEditing}
          mode="edit"
        />

        {/* EDIT RESPONSE MODAL - Using extracted EditResponseModal component */}
        <EditResponseModal
          isOpen={showEditResponseModal}
          onClose={() => setShowEditResponseModal(false)}
          onSubmit={handleSaveEditResponse}
          editResponseData={editResponseData}
          onEditResponseDataChange={setEditResponseData}
        />

        {/* LEFT: TASK QUEUE */}
        <TaskQueuePanel
          isOpen={isLeftPanelOpen}
          tasks={tasks}
          selectedTask={selectedTask}
          isProcessing={isProcessing}
          isResetting={isResetting}
          onSelectTask={startProcessing}
          onEditTask={handleOpenEdit}
           onResetAll={resetAll}
          onNewTask={() => {
            setSelectedTask(null);
            setChatHistory([]);
            setChatInput("");
            setChatClarify(null);
            setTimeout(() => chatInputRef.current?.focus(), 100);
          }}
        />

        {/* MIDDLE: AGENT THINKING TRACE */}
        <AgentThinkingTracePanel
          isLeftPanelOpen={isLeftPanelOpen}
          setIsLeftPanelOpen={setIsLeftPanelOpen}
          isRightPanelOpen={isRightPanelOpen}
          setIsRightPanelOpen={setIsRightPanelOpen}
          isProcessing={isProcessing}
          processingMs={processingMs}
          totalMs={totalMs}
          selectedTask={selectedTask}
          streamingSteps={streamingSteps}
          startProcessing={startProcessing}
          chatHistory={chatHistory}
          chatPhase={chatPhase}
           chatClarify={chatClarify}
           setChatClarify={setChatClarify}
           setChatHistory={setChatHistory}
           chatInput={chatInput}
          setChatInput={setChatInput}
          chatInputRef={chatInputRef}
          handleChatSubmit={handleChatSubmit}
          availableBrands={availableBrands}
        />
        {isRightPanelOpen && streamingSteps.some(s => s.event === "shadow_check") && (
          <TaskDetailPanel
            activeTaskDetail={activeTaskDetail}
            isProcessing={isProcessing}
            isSubmittingToClickUp={isSubmittingToClickUp}
            submitSuccess={submitSuccess}
            onEditResponse={() => {
              if (activeTaskDetail) {
                setEditResponseData(activeTaskDetail.ai_response || "");
                setShowEditResponseModal(true);
              }
            }}
            onRegenerate={(task) => startProcessing(task, true)}
             onSubmitToClickUp={submitToClickUp}
          />
        )}
      </div>
    </AssistantRuntimeProvider>
  );
}
