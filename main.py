from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from data_manager import (
    load_tasks,
    load_raw,
    save_tasks,
    shift_project_start,
    add_log_entry,
)
from utils import SchedulingError

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"
DIST_INDEX = STATIC_DIR / "dist" / "index.html"


@app.get("/health")
@app.head("/health")
def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "frontend_built": DIST_INDEX.is_file(),
        },
    )


@app.get("/")
def root():
    if not DIST_INDEX.is_file():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built. Run: cd frontend && npm ci && npm run build",
        )
    return RedirectResponse(url="/static/dist/index.html")


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


class TaskCreate(BaseModel):
    task: str
    hours: float = 8
    depends_on: List[int] = []
    status: str = "Not started"


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    hours: Optional[float] = None
    status: Optional[str] = None
    log: Optional[str] = None
    depends_on: Optional[List[int]] = None
    fixed_start: Optional[str] = None


class ProjectStartUpdate(BaseModel):
    project_start: str


class ShiftRequest(BaseModel):
    extra_days: int = 7


class LogRequest(BaseModel):
    message: str


class DelayRequest(BaseModel):
    hours: float
    reason: str


@app.get("/api/tasks")
def get_tasks():
    try:
        project_start, gap_days, tasks = load_tasks()
    except SchedulingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": tasks,
    }


@app.post("/api/tasks")
def create_task(body: TaskCreate):
    project_start, gap_days, tasks = load_raw()
    new_id = max((t["id"] for t in tasks), default=0) + 1
    for dep_id in body.depends_on:
        if not any(t["id"] == dep_id for t in tasks):
            raise HTTPException(status_code=400, detail=f"Unknown dependency task {dep_id}")

    new_task = {
        "id": new_id,
        "task": body.task.strip(),
        "hours": body.hours,
        "status": body.status,
        "log": "",
        "depends_on": list(body.depends_on),
    }
    tasks.append(new_task)
    save_tasks(project_start, gap_days, tasks)
    add_log_entry(f"Created task {new_id}: {body.task.strip()}")
    try:
        _, _, scheduled = load_tasks()
    except SchedulingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    created = next(t for t in scheduled if t["id"] == new_id)
    return {"message": "created", "task": created, "tasks": scheduled}


@app.put("/api/project-start")
def update_project_start(update: ProjectStartUpdate):
    project_start, gap_days, tasks = load_raw()
    save_tasks(update.project_start, gap_days, tasks)
    add_log_entry(f"Project start set to {update.project_start}")
    _, _, scheduled = load_tasks()
    return {
        "project_start": update.project_start,
        "gap_days": gap_days,
        "tasks": scheduled,
    }


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    project_start, gap_days, tasks = load_raw()
    found = False
    for t in tasks:
        if t["id"] == task_id:
            if update.task is not None:
                name = update.task.strip()
                if not name:
                    raise HTTPException(status_code=400, detail="Task name cannot be empty")
                t["task"] = name
            if update.hours is not None:
                t["hours"] = update.hours
            if update.status is not None:
                t["status"] = update.status
            if update.log is not None:
                t["log"] = update.log
            if update.depends_on is not None:
                t["depends_on"] = update.depends_on
            fields_set = update.model_dump(exclude_unset=True)
            if "fixed_start" in fields_set:
                if update.fixed_start:
                    t["fixed_start"] = update.fixed_start
                else:
                    t.pop("fixed_start", None)
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Task not found")

    save_tasks(project_start, gap_days, tasks)
    add_log_entry(f"Updated task {task_id}: {update.model_dump(exclude_unset=True)}")
    try:
        _, _, scheduled = load_tasks()
    except SchedulingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    project_end = max((t["end"] for t in scheduled), default="")
    return {
        "message": "updated",
        "tasks": scheduled,
        "project_end": project_end[:10] if project_end else "",
    }


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    project_start, gap_days, tasks = load_raw()
    removed = None
    for t in tasks:
        if t["id"] == task_id:
            removed = t
            break
    if not removed:
        raise HTTPException(status_code=404, detail="Task not found")

    dependents = [
        t["id"]
        for t in tasks
        if task_id in (t.get("depends_on") or []) and t["id"] != task_id
    ]
    tasks = [t for t in tasks if t["id"] != task_id]
    for t in tasks:
        deps = t.get("depends_on") or []
        if task_id in deps:
            t["depends_on"] = [d for d in deps if d != task_id]

    save_tasks(project_start, gap_days, tasks)
    add_log_entry(f"Deleted task {task_id}: {removed.get('task', '')}")
    try:
        _, _, scheduled = load_tasks()
    except SchedulingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    project_end = max((t["end"] for t in scheduled), default="")
    return {
        "message": "deleted",
        "tasks": scheduled,
        "project_end": project_end[:10] if project_end else "",
        "dependents_updated": dependents,
    }


@app.post("/api/shift")
def shift_timeline(request: ShiftRequest):
    new_start = shift_project_start(request.extra_days)
    add_log_entry(f"Shifted project start by {request.extra_days} days to {new_start}")
    project_start, gap_days, tasks = load_tasks()
    return {
        "message": f"Shifted project by {request.extra_days} days",
        "project_start": project_start,
        "tasks": tasks,
    }


@app.post("/api/tasks/{task_id}/log")
def append_task_log(task_id: int, body: LogRequest):
    project_start, gap_days, tasks = load_raw()
    for t in tasks:
        if t["id"] == task_id:
            stamp = datetime.now().isoformat(timespec="seconds")
            line = f"{stamp} - {body.message}\n"
            t["log"] = (t.get("log") or "") + line
            save_tasks(project_start, gap_days, tasks)
            add_log_entry(f"Task {task_id} ({t.get('task', '')}): {body.message}")
            try:
                _, _, scheduled = load_tasks()
            except SchedulingError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            updated = next(x for x in scheduled if x["id"] == task_id)
            return {"message": "logged", "task": updated}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/{task_id}/delay")
def log_task_delay(task_id: int, body: DelayRequest):
    if body.hours <= 0:
        raise HTTPException(status_code=400, detail="Delay hours must be greater than zero")
    reason = body.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Delay reason is required")

    project_start, gap_days, tasks = load_raw()
    found_task = None
    for t in tasks:
        if t["id"] == task_id:
            found_task = t
            t["delay_hours"] = float(t.get("delay_hours") or 0) + body.hours
            entry = {
                "date": datetime.now().date().isoformat(),
                "hours": body.hours,
                "reason": reason,
            }
            t.setdefault("delays", []).append(entry)
            stamp = datetime.now().isoformat(timespec="seconds")
            line = f"{stamp} - DELAY +{body.hours}h: {reason}\n"
            t["log"] = (t.get("log") or "") + line
            break
    if not found_task:
        raise HTTPException(status_code=404, detail="Task not found")

    save_tasks(project_start, gap_days, tasks)
    add_log_entry(
        f"Task {task_id} delay +{body.hours}h: {reason} "
        f"(total delay on task: {found_task.get('delay_hours')}h)"
    )
    try:
        _, _, scheduled = load_tasks()
    except SchedulingError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    updated = next(x for x in scheduled if x["id"] == task_id)
    project_end = max((t["end"] for t in scheduled), default="")
    return {
        "message": "delay logged",
        "task": updated,
        "tasks": scheduled,
        "project_end": project_end[:10] if project_end else "",
    }
