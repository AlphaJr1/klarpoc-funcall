import TaskList from "./TaskList";
import type { Task } from "../types";

interface TaskQueuePanelProps {
  isOpen: boolean;
  tasks: Task[];
  selectedTask: Task | null;
  isProcessing: boolean;
  isResetting: boolean;
  onSelectTask: (task: Task) => void;
  onEditTask: (task: Task) => void;
  onResetAll: () => void;
  onNewTask: () => void;
}

export default function TaskQueuePanel({
  isOpen,
  tasks,
  selectedTask,
  isProcessing,
  isResetting,
  onSelectTask,
  onEditTask,
  onResetAll,
  onNewTask,
}: TaskQueuePanelProps) {
  if (!isOpen) return null;

  return (
    <TaskList
      tasks={tasks}
      selectedTask={selectedTask}
      isProcessing={isProcessing}
      isResetting={isResetting}
      onSelectTask={onSelectTask}
      onEditTask={onEditTask}
      onResetAll={onResetAll}
      onNewTask={onNewTask}
    />
  );
}
