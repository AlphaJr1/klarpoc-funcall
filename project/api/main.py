import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import json
import asyncio
import concurrent.futures
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from router import route_stream
from clickup_sync import get_open_tasks, get_all_tasks, get_task_by_id, create_task

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


@app.post("/tasks", status_code=201)
def create_new_task(body: TaskCreate):
    task = create_task(
        task_name=body.task_name,
        brand=body.brand,
        date_range=body.date_range,
        priority=body.priority,
        description=body.description,
    )
    return {"task": task}


@app.get("/tasks")
def get_tasks():
    return {"tasks": get_all_tasks()}


@app.post("/tasks/reset")
def reset_tasks():
    from clickup_sync.clickup_tools import _load, _save
    data = _load()
    count = 0
    for task in data["tasks"]:
        if task.get("parent_task_id") or task["task_id"].startswith("esc_"):
            continue
        task["status"] = "open"
        task["ai_response"] = None
        task.pop("execution_trace", None)
        task["custom_fields"]["AI Confidence Score"] = None
        task["custom_fields"]["Resolution Status"] = None
        task["comments"] = []
        count += 1
    _save(data)
    return {"reset": count}


@app.get("/tasks/open")
def get_open():
    return {"tasks": get_open_tasks()}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task}


@app.post("/tasks/{task_id}/run")
async def run_task(task_id: str, force: bool = False):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_stream():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def run_generator():
            try:
                for event in route_stream(task, force=force):
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

    return StreamingResponse(event_stream(), media_type="text/event-stream")


LOYVERSE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "loyverse.json")


@app.get("/loyverse")
def get_loyverse():
    with open(LOYVERSE_PATH, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
