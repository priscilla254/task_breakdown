import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

from utils import schedule_tasks, SchedulingError

DATA_DIR = "data"
DEFAULT_PROJECT_ID = "phase1"
DEFAULT_PROJECT_START = "2026-06-01"
DEFAULT_GAP_DAYS = 1

TASK_FIELDS = ("id", "task", "hours", "status", "log", "depends_on")
# Training project: optional metadata (preserved on load/save when present)
TRAINING_TASK_FIELDS = ("department", "subject", "assignee", "phase", "module_index")

PROJECTS: Dict[str, Dict[str, str]] = {
    "phase1": {
        "id": "phase1",
        "name": "Data science and Innovation Phase 1",
        "tasks_file": "tasks-phase1.json",
        "legacy_tasks_file": "tasks.json",
    },
    "training": {
        "id": "training",
        "name": "Training platform content",
        "tasks_file": "tasks-training.json",
    },
}

# Sensible defaults for Phase 1 when tasks have no depends_on in JSON.
DEFAULT_DEPENDENCIES: Dict[int, List[int]] = {
    1: [],
    2: [1],
    3: [2],
    4: [3],
    5: [4],
    6: [5],
    7: [6],
    8: [7, 1],
    9: [8],
    10: [9],
    11: [10],
    12: [11],
    13: [12],
    14: [13],
    15: [14],
    16: [15],
    17: [16],
    18: [17],
    19: [18, 16],
    20: [19],
    21: [2],
    22: [19, 20],
    23: [22, 17],
    24: [23],
    25: [23],
    26: [25],
    27: [26],
    28: [23, 27],
    29: [28],
    30: [26],
    31: [29, 30],
    32: [31, 21],
    33: [31],
    34: [33],
    35: [34],
    36: [34],
    37: [36, 35],
}


class UnknownProjectError(ValueError):
    pass


def list_projects() -> List[Dict[str, str]]:
    return [{"id": p["id"], "name": p["name"]} for p in PROJECTS.values()]


def resolve_project_id(project_id: Optional[str]) -> str:
    pid = (project_id or DEFAULT_PROJECT_ID).strip()
    if pid not in PROJECTS:
        raise UnknownProjectError(f"Unknown project: {pid}")
    return pid


def _tasks_path(project_id: str) -> str:
    meta = PROJECTS[project_id]
    path = os.path.join(DATA_DIR, meta["tasks_file"])
    if os.path.exists(path):
        return path
    legacy = meta.get("legacy_tasks_file")
    if legacy:
        legacy_path = os.path.join(DATA_DIR, legacy)
        if os.path.exists(legacy_path):
            return legacy_path
    return path


def _log_path(project_id: str) -> str:
    return os.path.join(DATA_DIR, f"log-{project_id}.txt")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _clean_task(task: Dict) -> Dict:
    cleaned = {k: task[k] for k in TASK_FIELDS if k in task}
    cleaned["depends_on"] = list(cleaned.get("depends_on") or [])
    fixed = task.get("fixed_start")
    if fixed:
        cleaned["fixed_start"] = fixed
    completed_on = task.get("completed_on")
    if completed_on:
        cleaned["completed_on"] = completed_on
    delay_hours = task.get("delay_hours")
    if delay_hours:
        cleaned["delay_hours"] = float(delay_hours)
    delays = task.get("delays")
    if delays:
        cleaned["delays"] = list(delays)
    for key in TRAINING_TASK_FIELDS:
        if key in task and task[key] is not None:
            val = str(task[key]).strip()
            if val:
                cleaned[key] = val
    return cleaned


def _ensure_dependencies(tasks: List[Dict], project_id: str) -> List[Dict]:
    if project_id != "phase1":
        for t in tasks:
            t.setdefault("depends_on", [])
        return tasks
    if not any("depends_on" in t for t in tasks):
        for t in tasks:
            t["depends_on"] = list(DEFAULT_DEPENDENCIES.get(t["id"], []))
    else:
        for t in tasks:
            t.setdefault("depends_on", [])
    return tasks


def _migrate_legacy(data, project_id: str) -> Tuple[str, int, List[Dict]]:
    if isinstance(data, dict) and "tasks" in data:
        project_start = data.get("project_start", DEFAULT_PROJECT_START)
        gap_days = data.get("gap_days", DEFAULT_GAP_DAYS)
        tasks = [_clean_task(t) for t in data["tasks"]]
        tasks = _ensure_dependencies(tasks, project_id)
        return project_start, gap_days, tasks

    if isinstance(data, list):
        tasks = [_clean_task(t) for t in data]
        tasks = _ensure_dependencies(tasks, project_id)
        project_start = (
            data[0].get("start", DEFAULT_PROJECT_START) if data else DEFAULT_PROJECT_START
        )
        return project_start, DEFAULT_GAP_DAYS, tasks

    return DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, []


def _default_tasks() -> List[Dict]:
    return [
        {
            "id": 1,
            "task": "1. Finalise Excel template",
            "hours": 14,
            "status": "Not started",
            "log": "",
            "depends_on": [],
        },
        {
            "id": 2,
            "task": "2. Meeting with directors",
            "hours": 4,
            "status": "Not started",
            "log": "",
            "depends_on": [1],
        },
    ]


def load_raw(project_id: str = DEFAULT_PROJECT_ID) -> Tuple[str, int, List[Dict]]:
    project_id = resolve_project_id(project_id)
    ensure_data_dir()
    path = _tasks_path(project_id)

    if not os.path.exists(path):
        default_tasks = [] if project_id == "training" else _default_tasks()
        save_raw(project_id, DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks)
        return DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _migrate_legacy(data, project_id)


def save_raw(
    project_id: str,
    project_start: str,
    gap_days: int,
    tasks: List[Dict],
):
    project_id = resolve_project_id(project_id)
    ensure_data_dir()
    path = os.path.join(DATA_DIR, PROJECTS[project_id]["tasks_file"])
    payload = {
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": [_clean_task(t) for t in tasks],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_tasks(project_id: str = DEFAULT_PROJECT_ID) -> Tuple[str, int, List[Dict]]:
    project_start, gap_days, tasks = load_raw(project_id)
    scheduled = schedule_tasks(tasks, project_start, gap_days)
    return project_start, gap_days, scheduled


def save_tasks(
    project_id: str,
    project_start: str,
    gap_days: int,
    tasks: List[Dict],
):
    save_raw(project_id, project_start, gap_days, tasks)


def shift_project_start(project_id: str, extra_days: int) -> str:
    project_start, gap_days, tasks = load_raw(project_id)
    new_start = (
        datetime.fromisoformat(project_start) + timedelta(days=extra_days)
    ).date().isoformat()
    save_raw(project_id, new_start, gap_days, tasks)
    return new_start


def add_log_entry(project_id: str, message: str):
    project_id = resolve_project_id(project_id)
    ensure_data_dir()
    with open(_log_path(project_id), "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def get_log_entries(project_id: str) -> List[str]:
    project_id = resolve_project_id(project_id)
    path = _log_path(project_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()
