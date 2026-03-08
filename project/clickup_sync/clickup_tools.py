import json
import shutil
import uuid
from datetime import datetime, timezone
from .config import CLICKUP_FILE, CLICKUP_BACKUP_FILE, ESCALATION_THRESHOLD, RESOLVED_THRESHOLD

__all__ = [
    "get_open_tasks", "get_all_tasks", "get_task_by_id",
    "update_task", "add_comment", "create_escalation_task", "create_task",
    "mark_in_progress", "submit_task", "reset_task", "update_task_fields",
]


def _ensure_backup() -> None:
    """Buat backup jika belum ada."""
    import os
    if not os.path.exists(CLICKUP_BACKUP_FILE) and os.path.exists(CLICKUP_FILE):
        shutil.copy2(CLICKUP_FILE, CLICKUP_BACKUP_FILE)


def _load() -> dict:
    _ensure_backup()
    with open(CLICKUP_FILE) as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(CLICKUP_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _task_lifecycle_status(confidence_score: int) -> str:
    if confidence_score >= RESOLVED_THRESHOLD:
        return "resolved"
    elif confidence_score < ESCALATION_THRESHOLD:
        return "escalated"
    return "in_review"


def mark_in_progress(task_id: str) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = "in_progress"
            _save(data)
            return task
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def submit_task(task_id: str, ai_summary: str) -> dict:
    """AM submit: set status complete, simpan summary ke description."""
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = "complete"
            task["description"] = ai_summary
            task["custom_fields"]["Resolution Status"] = "Completed by AM"
            task.setdefault("comments", []).append({
                "comment_id": uuid.uuid4().hex[:8],
                "author": "AM",
                "text": f"[SUBMITTED] AM telah approve dan submit jawaban AI ke ClickUp.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            _save(data)
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def reset_task(task_id: str) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = "open"
            task["ai_response"] = None
            task.pop("execution_trace", None)
            task["custom_fields"]["AI Confidence Score"] = None
            task["custom_fields"]["Resolution Status"] = None
            task["comments"] = []
            task["description"] = ""
            _save(data)
            return task
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def update_task_fields(task_id: str, fields: dict) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            if "name" in fields:
                task["task_name"] = fields["name"]
            if "description" in fields:
                task["description"] = fields["description"]
            if "status" in fields:
                task["status"] = fields["status"]
            if "priority" in fields:
                task["custom_fields"]["Priority"] = fields["priority"]
            if "custom_fields" in fields:
                cf = fields["custom_fields"]
                for k, v in cf.items():
                    # Map uuid custom field ke nama (dummy logic)
                    if k == "brand" or "brand" in k.lower():
                        task["custom_fields"]["Brand"] = v
                    elif k == "date_range" or "date" in k.lower():
                        task["custom_fields"]["Date Range"] = v
                    else:
                        task["custom_fields"][k] = v
            _save(data)
            return task
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def get_open_tasks() -> list[dict]:
    data = _load()
    return [t for t in data.get("tasks", []) if t["status"] == "open"]


def get_all_tasks() -> list[dict]:
    return _load().get("tasks", [])


def get_task_by_id(task_id: str) -> dict | None:
    for t in _load().get("tasks", []):
        if t["task_id"] == task_id:
            return t
    return None


def update_task(
    task_id: str,
    ai_response: str,
    confidence_score: int,
    resolution_status: str,
    execution_trace: dict | None = None,
) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = _task_lifecycle_status(confidence_score)
            task["ai_response"] = ai_response
            task["custom_fields"]["AI Confidence Score"] = confidence_score
            task["custom_fields"]["Resolution Status"] = resolution_status
            task.setdefault("comments", [])
            if execution_trace:
                task["execution_trace"] = execution_trace
            _save(data)
            return task
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def add_comment(task_id: str, comment: str) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task.setdefault("comments", [])
            entry = {
                "comment_id": uuid.uuid4().hex[:8],
                "author": "AI Agent",
                "text": comment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            task["comments"].append(entry)
            _save(data)
            return entry
    raise ValueError(f"Task '{task_id}' tidak ditemukan.")


def create_task(
    task_name: str,
    brand: str,
    date_range: str,
    priority: str = "Medium",
    description: str = "",
) -> dict:
    import random, string
    data = _load()
    existing_ids = {t["task_id"] for t in data["tasks"]}
    while True:
        suffix = "".join(random.choices(string.ascii_lowercase, k=3))
        task_id = f"task_{suffix}"
        if task_id not in existing_ids:
            break
    new_task = {
        "task_id": task_id,
        "list_id": "list_001",
        "task_name": task_name,
        "description": description,
        "status": "open",
        "date_created": datetime.now(timezone.utc).isoformat(),
        "date_due": None,
        "assigned_to": "AI Agent",
        "custom_fields": {
            "Brand": brand,
            "Date Range": date_range,
            "Priority": priority,
            "Query Type": None,
            "AI Confidence Score": None,
            "Resolution Status": None,
        },
        "ai_response": None,
        "comments": [],
    }
    data["tasks"].append(new_task)
    _save(data)
    return new_task


def create_escalation_task(
    parent_task_id: str,
    question: str,
    brand: str,
    reason: str,
) -> dict:
    data = _load()
    new_task = {
        "task_id": f"esc_{uuid.uuid4().hex[:8]}",
        "list_id": "list_001",
        "task_name": f"[ESKALASI] {question[:80]}",
        "description": (
            f"Parent: {parent_task_id} | Brand: {brand}\n"
            f"Alasan eskalasi: {reason}"
        ),
        "status": "open",
        "date_created": datetime.now(timezone.utc).isoformat(),
        "date_due": None,
        "assigned_to": "AM Review",
        "custom_fields": {
            "Query Type": "Escalation",
            "Brand": brand,
            "Priority": "Urgent",
            "AI Confidence Score": None,
            "Resolution Status": "AM Review Required",
        },
        "ai_response": None,
        "parent_task_id": parent_task_id,
    }
    data["tasks"].append(new_task)
    _save(data)
    return new_task
