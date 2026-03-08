"""
clickup_api.py — Integrasi real ClickUp REST API v2
Mapping: ClickUp task → internal schema (kompatibel dengan clickup_tools.py)
"""
import os
import requests
import json
import uuid
from datetime import datetime, timezone

CLICKUP_API_KEY = os.environ.get("CLICKUP_API_KEY", "")
CLICKUP_LIST_ID = os.environ.get("CLICKUP_LIST_ID", "901816483690")

# Mapping nama project (lowercase keyword) → ClickUp list_id
# Update ini setiap ada list baru yang dibuat di ClickUp
PROJECT_LIST_MAP = {
    "fashion_brand_b q1 campaign": "901816546546",
    "fashion_brand_b q1": "901816546546",
    "fashion_brand_b": "901816546546",
    "q1 campaign": "901816546546",
    "klar-lixus poc development": "901816546550",
    "klar-lixus poc": "901816546550",
    "klar lixus poc": "901816546550",
    "poc development": "901816546550",
}

_BASE = "https://api.clickup.com/api/v2"

from typing import Any, Dict

AI_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ai_state.json")

def _load_ai_state() -> Dict[str, dict]:
    if os.path.exists(AI_STATE_FILE):
        try:
            with open(AI_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_ai_state(state: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(AI_STATE_FILE), exist_ok=True)
    with open(AI_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# Status mapping: internal → ClickUp status name
STATUS_MAP = {
    "open":        "to do",
    "in_progress": "in progress",
    "in_review":   "in progress",
    "resolved":    "complete",
    "escalated":   "in progress",
    "complete":    "complete",
}


def _headers():
    return {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}


def _parse_description(desc: str) -> dict:
    """Extract Brand & Date Range dari description jika custom_fields kosong.
    Format: 'Agent: X | Brand: Y | Date Range: Z | ...'
    """
    import re
    brand = None
    date_range = None
    if desc:
        m = re.search(r'Brand:\s*([^|\n]+)', desc)
        if m:
            brand = m.group(1).strip()
        m = re.search(r'Date Range:\s*([^|\n]+)', desc)
        if m:
            date_range = m.group(1).strip()
    return {"Brand": brand, "Date Range": date_range}


def _map_task(t: dict, state: dict | None = None) -> dict:
    """Konversi ClickUp API task → internal schema.
    ClickUp status SELALU jadi master. ai_state hanya enrichment (ai_response, trace, comments).
    """
    if state is None:
        state = {}

    raw_cf = {cf["name"]: cf.get("value") for cf in t.get("custom_fields", [])}
    priority_map = {None: "Medium", "1": "Urgent", "2": "High", "3": "Medium", "4": "Low"}
    prio_id = str(t.get("priority", {}).get("id", "")) if t.get("priority") else None

    # ClickUp is source-of-truth for status
    status_raw = t.get("status", {}).get("status", "to do").lower()
    if status_raw == "to do":
        status_internal = "open"
    elif status_raw == "complete":
        status_internal = "complete"
    elif status_raw == "in progress":
        # Only here we enrich with ai_state (escalated / in_review / resolved)
        status_internal = state.get("internal_status") or "in_progress"
    else:
        status_internal = status_raw  # passthrough

    # Fallback: parse description jika custom_fields kosong
    desc = t.get("description", "")
    parsed = _parse_description(desc)
    brand = raw_cf.get("Brand") or parsed["Brand"]
    date_range = raw_cf.get("Date Range") or parsed["Date Range"]

    return {
        "task_id": t["id"],
        "list_id": CLICKUP_LIST_ID,
        "task_name": t.get("name", ""),
        "description": desc,
        "status": status_internal,
        "date_created": t.get("date_created", ""),
        "date_due": t.get("due_date"),
        "assigned_to": (t.get("assignees") or [{}])[0].get("username", "AI Agent"),
        "custom_fields": {
            "Brand":               brand,
            "Date Range":          date_range,
            "Priority":            priority_map.get(prio_id, "Medium"),
            "Query Type":          raw_cf.get("Query Type"),
            "AI Confidence Score": raw_cf.get("AI Confidence Score"),
            "Resolution Status":   raw_cf.get("Resolution Status"),
        },
        "ai_response": state.get("ai_response"),
        "execution_trace": state.get("execution_trace"),
        "comments": state.get("comments", []),
        "_clickup_status_id": t.get("status", {}).get("id"),
    }


def get_all_tasks() -> list[dict]:
    """Fetch semua task termasuk closed/complete."""
    url = f"{_BASE}/list/{CLICKUP_LIST_ID}/task?archived=false&page=0&include_closed=true"
    r = requests.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    st = _load_ai_state()
    return [_map_task(t, st.get(t["id"])) for t in r.json().get("tasks", [])]


def get_open_tasks() -> list[dict]:
    return [t for t in get_all_tasks() if t["status"] in ("open", "in_progress", "escalated", "in_review")]


def get_task_by_id(task_id: str) -> dict | None:
    url = f"{_BASE}/task/{task_id}"
    r = requests.get(url, headers=_headers(), timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    st = _load_ai_state()
    return _map_task(r.json(), st.get(task_id))


def _update_status(task_id: str, internal_status: str):
    cu_status = STATUS_MAP.get(internal_status, "in progress")
    url = f"{_BASE}/task/{task_id}"
    requests.put(url, headers=_headers(), json={"status": cu_status}, timeout=10)


def mark_in_progress(task_id: str) -> dict:
    _update_status(task_id, "in_progress")
    st = _load_ai_state()
    if task_id not in st:
        st[task_id] = {}
    st[task_id]["internal_status"] = "in_progress"
    _save_ai_state(st)
    return {"task_id": task_id, "status": "in_progress"}


def reset_task(task_id: str) -> dict:
    """
    Reset task ke kondisi awal (to do): bersihkan description AI,
    kembalikan status ke 'to do'.
    """
    url = f"{_BASE}/task/{task_id}"
    requests.put(url, headers=_headers(),
                 json={"status": "to do", "description": ""},
                 timeout=10)
    # Hapus semua comment via list + delete
    try:
        coms = requests.get(f"{url}/comment", headers=_headers(), timeout=10).json()
        for c in coms.get("comments", []):
            requests.delete(f"{_BASE}/comment/{c['id']}", headers=_headers(), timeout=5)
    except Exception:
        pass
        
    st = _load_ai_state()
    if task_id in st:
        st.pop(task_id, None)
        _save_ai_state(st)
        
    return {"task_id": task_id, "status": "open"}


def update_task_fields(task_id: str, fields: dict) -> dict:
    """
    Update arbitrary fields ClickUp task.
    fields: dict dengan key ClickUp-native:
      name, description, status, priority (1-4 int),
      due_date (epoch ms int), assignees, custom_fields list
    """
    payload = {}
    if "name" in fields:
        payload["name"] = fields["name"]
    if "description" in fields:
        payload["description"] = fields["description"]
    if "status" in fields:
        payload["status"] = fields["status"]
    if "priority" in fields:
        prio_map = {"Urgent": 1, "High": 2, "Medium": 3, "Low": 4}
        payload["priority"] = prio_map.get(fields["priority"], fields["priority"])
    if "due_date" in fields:
        payload["due_date"] = fields["due_date"]

    url = f"{_BASE}/task/{task_id}"
    if payload:
        r = requests.put(url, headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()

    # Custom fields via dedicated endpoint
    if "custom_fields" in fields:
        for cf_id, cf_val in fields["custom_fields"].items():
            requests.post(
                f"{url}/field/{cf_id}",
                headers=_headers(),
                json={"value": cf_val},
                timeout=5,
            )

    task = get_task_by_id(task_id)
    return task or {"task_id": task_id}


def update_task(
    task_id: str,
    ai_response: str,
    confidence_score: int,
    resolution_status: str,
    execution_trace: dict | None = None,
) -> dict:
    # Update status berdasarkan confidence
    if confidence_score >= 95:
        internal = "resolved"
    elif confidence_score < 80:
        internal = "escalated"
    else:
        internal = "in_review"
    _update_status(task_id, internal)
    
    st = _load_ai_state()
    if task_id not in st:
        st[task_id] = {}
    st[task_id]["internal_status"] = internal
    st[task_id]["ai_response"] = ai_response
    st[task_id]["execution_trace"] = execution_trace
    _save_ai_state(st)
    
    return {"task_id": task_id, "status": internal, "confidence_score": confidence_score}


def get_task_details(task_id: str) -> dict | None:
    """Write tool: ambil detail task (alias get_task_by_id, untuk LLM function calling)."""
    return get_task_by_id(task_id)


def assign_task(task_id: str, assignee_id: str) -> dict:
    """Write tool: assign task ke user tertentu via ClickUp API."""
    url = f"{_BASE}/task/{task_id}"
    r = requests.put(url, headers=_headers(), json={"assignees": {"add": [int(assignee_id)]}}, timeout=10)
    r.raise_for_status()
    return {"task_id": task_id, "assigned_to": assignee_id}


def add_comment(task_id: str, comment: str) -> dict:
    url = f"{_BASE}/task/{task_id}/comment"
    try:
        r = requests.post(url, headers=_headers(),
                          json={"comment_text": comment, "notify_all": False}, timeout=10)
    except Exception:
        pass

    st = _load_ai_state()
    if task_id not in st:
        st[task_id] = {}

    comments = st[task_id].get("comments")
    if not isinstance(comments, list):
        comments = []
        st[task_id]["comments"] = comments

    entry = {
        "comment_id": uuid.uuid4().hex[:8],
        "author": "AI Agent",
        "text": comment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    comments.append(entry)
    _save_ai_state(st)

    return entry


def submit_task(task_id: str, ai_summary: str) -> dict:
    """AM submit: set status complete + simpan summary ke description ClickUp."""
    url = f"{_BASE}/task/{task_id}"
    requests.put(url, headers=_headers(),
                 json={"status": "complete", "description": ai_summary}, timeout=10)
    add_comment(task_id, "[SUBMITTED] AM telah approve dan submit jawaban AI ke ClickUp.")
    
    st = _load_ai_state()
    if task_id not in st:
        st[task_id] = {}
    st[task_id]["internal_status"] = "complete"
    st[task_id]["ai_response"] = ai_summary
    _save_ai_state(st)
    
    return {"task_id": task_id, "status": "complete"}


def create_task(
    task_name: str,
    brand: str,
    date_range: str,
    priority: str = "Medium",
    description: str = "",
) -> dict:
    prio_map = {"Urgent": 1, "High": 2, "Medium": 3, "Low": 4}
    url = f"{_BASE}/list/{CLICKUP_LIST_ID}/task"
    payload = {
        "name": task_name,
        "description": description or f"Brand: {brand} | Date Range: {date_range}",
        "priority": prio_map.get(priority, 3),
        "status": "to do",
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=10)
    r.raise_for_status()
    return _map_task(r.json())


def create_escalation_task(parent_task_id: str, question: str, brand: str, reason: str) -> dict:
    url = f"{_BASE}/list/{CLICKUP_LIST_ID}/task"
    payload = {
        "name": f"[ESKALASI] {question[:80]}",
        "description": f"Parent: {parent_task_id} | Brand: {brand}\nAlasan: {reason}",
        "priority": 1,  # urgent
        "status": "to do",
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=10)
    r.raise_for_status()
    return _map_task(r.json())


# ── State 3: ClickUp Read Tools (data source untuk project management queries) ──

def _resolve_list_id(project_id: str) -> str:
    """
    Resolve project_id (nama project atau list_id numeric) → ClickUp list_id.
    Priority: numeric ID → PROJECT_LIST_MAP → substring match → default list.
    """
    if project_id.strip().lstrip("-").isdigit():
        return project_id
    # Cek exact / substring match di PROJECT_LIST_MAP
    pid_lower = project_id.lower()
    for keyword, list_id in PROJECT_LIST_MAP.items():
        if keyword in pid_lower or pid_lower in keyword:
            return list_id
    # Fallback: default list
    return CLICKUP_LIST_ID


def _get_list_tasks(list_id: str, include_closed: bool = True) -> list[dict]:
    resolved = _resolve_list_id(list_id)
    url = f"{_BASE}/list/{resolved}/task?archived=false&include_closed={str(include_closed).lower()}"
    r = requests.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json().get("tasks", [])


def get_project_status(project_id: str) -> dict:
    """
    State 3 read tool: ambil status & progress project dari ClickUp list.
    project_id = ClickUp list_id ATAU nama project (LLM-friendly).
    """
    list_id = _resolve_list_id(project_id)
    tasks = _get_list_tasks(list_id)

    # Kalau list_id == default list (tidak ter-resolve ke project khusus) → filter by name
    if list_id == CLICKUP_LIST_ID and not project_id.strip().lstrip("-").isdigit() and project_id.lower() not in ("all", ""):
        keyword = project_id.lower()
        tasks = [t for t in tasks if keyword in t.get("name", "").lower()]

    total = len(tasks)
    if total == 0:
        return {"project_id": project_id, "total_tasks": 0, "progress_percent": 0, "tasks": [],
                "note": f"No tasks found matching '{project_id}'. Showing all tasks from default list."}

    done_statuses = {"complete", "closed", "done"}
    completed = sum(1 for t in tasks if t.get("status", {}).get("status", "").lower() in done_statuses)
    in_prog = sum(1 for t in tasks if t.get("status", {}).get("status", "").lower() == "in progress")
    progress = round(completed / total * 100)

    task_list = [
        {
            "task_id": t["id"],
            "task_name": t.get("name", ""),
            "status": t.get("status", {}).get("status", ""),
            "assignee": (t.get("assignees") or [{}])[0].get("username", ""),
            "due_date": t.get("due_date"),
        }
        for t in tasks
    ]
    return {
        "project_id": project_id,
        "resolved_list_id": list_id,
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_prog,
        "todo_tasks": total - completed - in_prog,
        "progress_percent": progress,
        "tasks": task_list,
    }


def get_overdue_tasks(project_id: str) -> list[dict]:
    """
    State 3 read tool: ambil semua task yang overdue di list tertentu atau semua list.
    project_id = list_id, nama project, atau 'all'.
    """
    from datetime import timezone as _tz
    now_ms = int(datetime.now(_tz.utc).timestamp() * 1000)
    done_statuses = {"complete", "closed", "done"}

    if project_id == "all":
        # Scan semua list yang terdaftar
        all_list_ids = {CLICKUP_LIST_ID}
        all_list_ids.update(PROJECT_LIST_MAP.values())
        overdue = []
        seen_ids = set()
        for lid in all_list_ids:
            try:
                tasks = _get_list_tasks(lid, include_closed=False)
            except Exception:
                continue
            for t in tasks:
                tid = t.get("id")
                if tid in seen_ids:
                    continue
                status = t.get("status", {}).get("status", "").lower()
                if status in done_statuses:
                    continue
                due = t.get("due_date")
                if due and int(due) < now_ms:
                    days_overdue = (now_ms - int(due)) // (1000 * 86400)
                    seen_ids.add(tid)
                    overdue.append({
                        "task_id": tid,
                        "task_name": t.get("name", ""),
                        "status": status,
                        "assignee": (t.get("assignees") or [{}])[0].get("username", ""),
                        "due_date": t.get("due_date"),
                        "start_date": t.get("start_date"),
                        "date_created": t.get("date_created"),
                        "date_updated": t.get("date_updated"),
                        "days_overdue": days_overdue,
                    })
        overdue.sort(key=lambda x: x["days_overdue"], reverse=True)
        return overdue

    elif project_id.strip().lstrip("-").isdigit():
        list_id = project_id
        name_filter = None
    else:
        list_id = _resolve_list_id(project_id)
        # Kalau ter-resolve ke list khusus, tidak perlu name filter
        name_filter = None if list_id != CLICKUP_LIST_ID else project_id.lower()
    tasks = _get_list_tasks(list_id, include_closed=False)

    overdue = []
    for t in tasks:
        if name_filter and name_filter not in t.get("name", "").lower():
            continue
        status = t.get("status", {}).get("status", "").lower()
        if status in done_statuses:
            continue
        due = t.get("due_date")
        if due and int(due) < now_ms:

            days_overdue = (now_ms - int(due)) // (1000 * 86400)
            overdue.append({
                "task_id": t["id"],
                "task_name": t.get("name", ""),
                "status": status,
                "assignee": (t.get("assignees") or [{}])[0].get("username", ""),
                "due_date": t.get("due_date"),
                "start_date": t.get("start_date"),
                "date_created": t.get("date_created"),
                "date_updated": t.get("date_updated"),
                "days_overdue": days_overdue,
            })

    overdue.sort(key=lambda x: x["days_overdue"], reverse=True)
    return overdue


def get_tasks_by_assignee(assignee: str, week: str | None = None, status_filter: str | None = None) -> list[dict]:
    """
    State 3 read tool: ambil semua task untuk satu assignee dari semua list project.
    Scan: default list + semua list di PROJECT_LIST_MAP.
    Match: ClickUp assignees field ATAU 'Assignee: X' di description (untuk dummy tasks).
    """
    # Kumpulkan semua unique list_id yang perlu di-scan
    all_list_ids = {CLICKUP_LIST_ID}
    all_list_ids.update(PROJECT_LIST_MAP.values())

    assignee_lower = assignee.lower()
    result = []
    seen_ids = set()

    for list_id in all_list_ids:
        try:
            tasks = _get_list_tasks(list_id, include_closed=True)
        except Exception:
            continue

        for t in tasks:
            tid = t.get("id")
            if tid in seen_ids:
                continue

            # Match via ClickUp assignees
            assignees = [a.get("username", "").lower() for a in (t.get("assignees") or [])]
            match_assignee = any(assignee_lower in a for a in assignees)

            # Fallback: match "Assignee: X" di description
            if not match_assignee:
                desc = (t.get("description") or "").lower()
                match_assignee = f"assignee: {assignee_lower}" in desc

            if not match_assignee:
                continue

            status = t.get("status", {}).get("status", "").lower()
            if status_filter and status_filter.lower() not in status:
                continue

            seen_ids.add(tid)
            result.append({
                "task_id": tid,
                "task_name": t.get("name", ""),
                "status": status,
                "assignee": assignee,
                "list_id": list_id,
                "due_date": t.get("due_date"),
                "start_date": t.get("start_date"),
                "date_created": t.get("date_created"),
                "date_updated": t.get("date_updated"),
            })

    return result
