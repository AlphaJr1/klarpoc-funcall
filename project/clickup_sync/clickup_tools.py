import json
import shutil
import uuid
from datetime import datetime, timezone
from .config import CLICKUP_FILE, CLICKUP_BACKUP_FILE, ESCALATION_THRESHOLD, RESOLVED_THRESHOLD


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
) -> dict:
    data = _load()
    for task in data["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = _task_lifecycle_status(confidence_score)
            task["ai_response"] = ai_response
            task["custom_fields"]["AI Confidence Score"] = confidence_score
            task["custom_fields"]["Resolution Status"] = resolution_status
            task.setdefault("comments", [])
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
