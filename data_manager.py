import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from utils import schedule_tasks, SchedulingError

DATA_DIR = "data"
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
DEFAULT_PROJECT_START = "2026-06-01"
DEFAULT_GAP_DAYS = 1

TASK_FIELDS = ("id", "task", "hours", "status", "log", "depends_on")

# Sensible defaults: sequential phases + parallel tracks (e.g. TDL design, Power BI wireframes).
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


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _clean_task(task: Dict) -> Dict:
    cleaned = {k: task[k] for k in TASK_FIELDS if k in task}
    cleaned["depends_on"] = list(cleaned.get("depends_on") or [])
    fixed = task.get("fixed_start")
    if fixed:
        cleaned["fixed_start"] = fixed
    delay_hours = task.get("delay_hours")
    if delay_hours:
        cleaned["delay_hours"] = float(delay_hours)
    delays = task.get("delays")
    if delays:
        cleaned["delays"] = list(delays)
    return cleaned


def _ensure_dependencies(tasks: List[Dict]) -> List[Dict]:
    if not any("depends_on" in t for t in tasks):
        for t in tasks:
            t["depends_on"] = list(DEFAULT_DEPENDENCIES.get(t["id"], []))
    else:
        for t in tasks:
            t.setdefault("depends_on", [])
    return tasks


def _migrate_legacy(data) -> Tuple[str, int, List[Dict]]:
    if isinstance(data, dict) and "tasks" in data:
        project_start = data.get("project_start", DEFAULT_PROJECT_START)
        gap_days = data.get("gap_days", DEFAULT_GAP_DAYS)
        tasks = [_clean_task(t) for t in data["tasks"]]
        tasks = _ensure_dependencies(tasks)
        return project_start, gap_days, tasks

    if isinstance(data, list):
        tasks = [_clean_task(t) for t in data]
        tasks = _ensure_dependencies(tasks)
        project_start = (
            data[0].get("start", DEFAULT_PROJECT_START) if data else DEFAULT_PROJECT_START
        )
        return project_start, DEFAULT_GAP_DAYS, tasks

    return DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, []


def load_raw() -> Tuple[str, int, List[Dict]]:
    ensure_data_dir()
    if not os.path.exists(TASKS_FILE):
        default_tasks = [
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
        save_raw(DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks)
        return DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _migrate_legacy(data)


def save_raw(project_start: str, gap_days: int, tasks: List[Dict]):
    ensure_data_dir()
    payload = {
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": [_clean_task(t) for t in tasks],
    }
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_tasks() -> Tuple[str, int, List[Dict]]:
    project_start, gap_days, tasks = load_raw()
    scheduled = schedule_tasks(tasks, project_start, gap_days)
    return project_start, gap_days, scheduled


def save_tasks(project_start: str, gap_days: int, tasks: List[Dict]):
    save_raw(project_start, gap_days, tasks)


def shift_project_start(extra_days: int) -> str:
    project_start, gap_days, tasks = load_raw()
    new_start = (
        datetime.fromisoformat(project_start) + timedelta(days=extra_days)
    ).date().isoformat()
    save_raw(new_start, gap_days, tasks)
    return new_start


def add_log_entry(message: str):
    ensure_data_dir()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def get_log_entries() -> List[str]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.readlines()
