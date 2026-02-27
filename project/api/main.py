import sys
import os

# Tambahkan project root ke sys.path agar import package bisa berjalan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from router import route
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
async def run_task(task_id: str):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        result = route(task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    async def event_stream():
        yield f"data: {json.dumps({'event': 'state_detected', 'state': result.get('state', 'UNKNOWN'), 'matched_keyword': result.get('matched_keyword', '')})}\n\n"
        await asyncio.sleep(0.8)

        for tc in result.get("tool_calls", []):
            yield f"data: {json.dumps({'event': 'tool_call', 'tool': tc['tool'], 'input': tc.get('input', {})})}\n\n"
            await asyncio.sleep(1.0)
            yield f"data: {json.dumps({'event': 'tool_result', 'tool': tc['tool'], 'result': tc.get('result', {})})}\n\n"
            await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'event': 'confidence', 'score': result.get('confidence_score', 0)})}\n\n"
        await asyncio.sleep(0.5)

        done = {
            "event": "done",
            "resolution": result.get("resolution_status", ""),
            "response": result.get("ai_response", ""),
            "escalation_task": result.get("escalation_task"),
        }
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


LOYVERSE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "loyverse.json")


@app.get("/loyverse")
def get_loyverse():
    with open(LOYVERSE_PATH, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
