import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import json
import logging
import asyncio
import concurrent.futures
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from router import route_stream
# Real ClickUp API (primary)
try:
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from clickup_sync.clickup_api import (
        get_all_tasks as cu_get_all,
        get_open_tasks as cu_get_open,
        get_task_by_id as cu_get_by_id,
        create_task as cu_create,
        submit_task as cu_submit,
        mark_in_progress as cu_mark_inprogress,
        reset_task as cu_reset_task,
        update_task_fields as cu_update_fields,
    )
    _USE_REAL_API = True
except Exception as _e:
    from clickup_sync import get_all_tasks as cu_get_all, get_open_tasks as cu_get_open
    from clickup_sync import get_task_by_id as cu_get_by_id, create_task as cu_create
    from clickup_sync import submit_task as cu_submit, mark_in_progress as cu_mark_inprogress
    from clickup_sync import reset_task as cu_reset_task, update_task_fields as cu_update_fields
    _USE_REAL_API = False

# Frontend UI logger
_UI_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "frontend_ui.log")
os.makedirs(os.path.dirname(_UI_LOG_PATH), exist_ok=True)
_ui_logger = logging.getLogger("frontend_ui")
if not _ui_logger.handlers:
    _ufh = logging.FileHandler(_UI_LOG_PATH)
    _ufh.setFormatter(logging.Formatter("%(message)s"))
    _ui_logger.addHandler(_ufh)
    _ui_logger.setLevel(logging.INFO)

app = FastAPI(title="State Machine Router API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskCreate(BaseModel):
    task_name: str
    brand: str
    date_range: str
    priority: str = "Medium"
    description: str = ""


class RunTaskBody(BaseModel):
    query_override: str | None = None


class LogEntry(BaseModel):
    task_id: str
    event: str
    elapsed_ms: int
    delta_ms: int
    detail: str = ""


@app.post("/log")
def write_ui_log(entry: LogEntry):
    _ui_logger.info(
        "[%6dms | Δ%5dms] %-30s %s",
        entry.elapsed_ms, entry.delta_ms, entry.event, entry.detail,
    )
    return {"ok": True}


@app.post("/tasks", status_code=201)
def create_new_task(body: TaskCreate):
    task = cu_create(
        task_name=body.task_name,
        brand=body.brand,
        date_range=body.date_range,
        priority=body.priority,
        description=body.description,
    )
    return {"task": task}


@app.get("/tasks")
def get_tasks():
    return {"tasks": cu_get_all(), "source": "clickup_api" if _USE_REAL_API else "local_json"}


@app.post("/tasks/reset")
def reset_tasks():
    tasks = cu_get_all()
    to_reset = [t for t in tasks if not t.get("parent_task_id") and not t["task_id"].startswith("esc_")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda t: cu_reset_task(t["task_id"]), to_reset))
    return {"reset": len(to_reset)}

@app.post("/tasks/{task_id}/reset")
def reset_single_task(task_id: str):
    task = cu_get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    result = cu_reset_task(task_id)
    return {"task": cu_get_by_id(task_id)}

class TaskEdit(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    brand: str | None = None
    date_range: str | None = None

@app.patch("/tasks/{task_id}")
def edit_task(task_id: str, body: TaskEdit):
    task = cu_get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    fields = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.description is not None:
        fields["description"] = body.description
    if body.priority is not None:
        fields["priority"] = body.priority
    if body.brand is not None or body.date_range is not None:
        cf = {}
        if body.brand is not None:
            cf["brand"] = body.brand
        if body.date_range is not None:
            cf["date_range"] = body.date_range
        fields["custom_fields"] = cf

    updated = cu_update_fields(task_id, fields)
    return {"task": updated}

class ChatHistoryUpdate(BaseModel):
    chat_history: list

@app.patch("/tasks/{task_id}/chat_history")
def update_task_chat_history(task_id: str, body: ChatHistoryUpdate):
    try:
        from clickup_sync.clickup_api import update_chat_history
        update_chat_history(task_id, body.chat_history)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/open")
def get_open():
    return {"tasks": cu_get_open()}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = cu_get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task}


@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str, force: bool = False, body: RunTaskBody = RunTaskBody()):
    task = cu_get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_stream():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def run_generator():
            try:
                for event in route_stream(task, force=force, query_override=body.query_override):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        loop.run_in_executor(executor, run_generator)

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


class SubmitTaskBody(BaseModel):
    ai_summary: str


@app.post("/tasks/{task_id}/submit")
def submit_task_endpoint(task_id: str, body: SubmitTaskBody):
    task = cu_get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = cu_submit(task_id, body.ai_summary)
    return {"task": updated}


LOYVERSE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "loyverse.json")


@app.get("/loyverse")
def get_loyverse():
    with open(LOYVERSE_PATH, "r") as f:
        return json.load(f)


@app.get("/brands")
def get_brands():
    from router.config import BRAND_STORE_MAP
    return {"brands": list(BRAND_STORE_MAP.keys())}


class ChatTaskMessage(BaseModel):
    message: str
    history: list = []  # [{role: "user"|"assistant", content: str}]


@app.post("/tasks/chat")
def chat_task_creation(body: ChatTaskMessage):
    """
    AI-assisted task creation via chat.
    - Terima prompt user + history percakapan
    - AI extract: task_query, brand, date_range, priority
    - Kalau kurang info -> return clarification question + options
    - Kalau sudah lengkap -> buat task, return task + ready: true
    """
    from router.llm import get_llm_client
    from router.config import BRAND_STORE_MAP, OLLAMA_MODEL
    from datetime import datetime

    client = get_llm_client()
    today = datetime.now().strftime("%Y-%m-%d")
    brands_str = ", ".join(BRAND_STORE_MAP.keys())

    system_prompt = (
        "Kamu adalah asisten AI untuk membuat task analisis data marketing.\n"
        "Tugasmu adalah mengekstrak informasi berikut dari percakapan dengan user:\n"
        "1. task_query: pertanyaan spesifik yang ingin dijawab (wajib)\n"
        "2. brand: nama brand dari sistem yang relevan (wajib)\n"
        "3. date_range: rentang tanggal dalam format YYYY-MM-DD atau YYYY-MM-DD to YYYY-MM-DD (wajib)\n"
        "4. priority: High / Medium / Low (default Medium)\n\n"
        f"Brand yang tersedia dalam sistem: {brands_str}\n"
        f"Hari ini: {today}\n\n"
        "Aturan:\n"
        "- Jika semua info (task_query, brand, date_range) sudah lengkap dan jelas, return JSON:\n"
        '  {"status": "ready", "task_query": "...", "brand": "...", "date_range": "...", "priority": "Medium"}\n'
        "- Jika ada info yang kurang atau ambigu, tanya user dengan return JSON:\n"
        '  {"status": "clarify", "message": "...", "missing_fields": ["brand", "date_range"], '
        '"options": {"brand": ["Kopi_Brand_A", "Fashion_Brand_B"], "date_range": ["2026-01-01 to 2026-01-31", "Minggu lalu"]}}\n'
        "- Setelah user menjawab clarification, gabungkan answer dengan context sebelumnya.\n"
        "- Selalu gunakan Bahasa Indonesia yang baik dan benar untuk pesan ke user. JANGAN PERNAH MENGGUNAKAN BAHASA MANDARIN/CHINESE (Contoh: 进行数据, 请问, dll).\n"
        "- DILARANG KERAS menggunakan karakter Cyrillic (Rusia), Mandarin, atau aksara selain Latin.\n"
        "- brand harus PERSIS sesuai nama dalam daftar brand yang tersedia.\n"
        "- Respond JSON only, no other text."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for h in body.history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": body.message})

    try:
        resp = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
        )
        text = resp.choices[0].message.content.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]
            if text.startswith("json"):
                text = text[4:].strip()
        start, end = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[start:end]) if start >= 0 and end > start else {}
    except Exception as e:
        return {"status": "error", "message": f"AI error: {e}"}

    if data.get("status") == "ready":
        brand = data.get("brand", "")
        if brand not in BRAND_STORE_MAP:
            # cari partial match
            for k in BRAND_STORE_MAP:
                if brand.lower() in k.lower() or k.lower() in brand.lower():
                    brand = k
                    break
        task = cu_create(
            task_name=data.get("task_query", body.message),
            brand=brand,
            date_range=data.get("date_range", ""),
            priority=data.get("priority", "Medium"),
            description="",
        )
        return {"status": "ready", "task": task}

    return {
        "status": data.get("status", "clarify"),
        "message": data.get("message", "Mohon lengkapi informasi berikut:"),
        "missing_fields": data.get("missing_fields", []),
        "options": data.get("options", {}),
        "assistant_message": data.get("message", ""),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
