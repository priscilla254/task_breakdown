import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

from duration import hours_to_days, normalize_days, parse_task_days
from schedule_cache import invalidate_schedule_cache
from utils import schedule_tasks, SchedulingError

DATA_DIR = "data"
DEFAULT_PROJECT_ID = "phase1"
DEFAULT_PROJECT_START = "2026-06-01"
DEFAULT_GAP_DAYS = 1

TASK_FIELDS = ("id", "task", "days", "status", "log", "depends_on")
# Training project: optional metadata (preserved on load/save when present)
TRAINING_TASK_FIELDS = ("department", "subject", "phase", "module_index", "step_id")
OPTIONAL_TASK_FIELDS = ("assignee",)

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
    28: [40],
    29: [27],
    30: [28, 31],
    40: [29],
    31: [40],
    32: [30],
    41: [32],
    42: [41],
    33: [42],
    34: [25],
    35: [33],
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


def _clean_delay_entry(entry: Dict) -> Optional[Dict]:
    if not isinstance(entry, dict):
        return None
    date = entry.get("date")
    reason = entry.get("reason", "")
    if not date:
        return None
    if "days" in entry and entry["days"] is not None:
        days = normalize_days(entry["days"])
    elif "hours" in entry and entry["hours"] is not None:
        days = hours_to_days(entry["hours"])
    else:
        return None
    return {"date": date, "days": days, "reason": reason}


def _clean_task(task: Dict) -> Dict:
    if "days" in task and task["days"] is not None:
        days = parse_task_days(task["days"])
    elif "hours" in task and task["hours"] is not None:
        days = float(hours_to_days(task["hours"]))
    else:
        days = 1.0

    cleaned = {k: task[k] for k in TASK_FIELDS if k in task and k != "days"}
    cleaned["days"] = days
    cleaned["depends_on"] = list(cleaned.get("depends_on") or task.get("depends_on") or [])
    fixed = task.get("fixed_start")
    if fixed:
        cleaned["fixed_start"] = fixed
    fixed_end = task.get("fixed_end")
    if fixed_end:
        cleaned["fixed_end"] = str(fixed_end)[:10]
    completed_on = task.get("completed_on")
    if completed_on:
        cleaned["completed_on"] = completed_on
    delay_days = task.get("delay_days")
    if delay_days:
        cleaned["delay_days"] = int(delay_days)
    elif task.get("delay_hours"):
        cleaned["delay_days"] = hours_to_days(task["delay_hours"])
    delays = task.get("delays")
    if delays:
        cleaned["delays"] = [
            e for e in (_clean_delay_entry(d) for d in delays) if e is not None
        ]
    for key in TRAINING_TASK_FIELDS:
        if key in task and task[key] is not None:
            if key == "module_index":
                try:
                    cleaned[key] = int(task[key])
                except (ValueError, TypeError):
                    pass
            else:
                val = str(task[key]).strip()
                if val:
                    cleaned[key] = val
    for key in OPTIONAL_TASK_FIELDS:
        if key in task and task[key] is not None:
            val = str(task[key]).strip()
            if val:
                cleaned[key] = val
    display_order = task.get("display_order")
    if display_order is not None:
        cleaned["display_order"] = int(display_order)
    for key in ("starts_with", "ends_with", "starts_when_start_of"):
        if key in task and task[key] is not None:
            cleaned[key] = int(task[key])
    if task.get("parallel_group"):
        cleaned["parallel_group"] = str(task["parallel_group"]).strip()
    if task.get("milestone"):
        cleaned["milestone"] = bool(task["milestone"])
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
            "days": 2,
            "status": "Not started",
            "log": "",
            "depends_on": [],
        },
        {
            "id": 2,
            "task": "2. Meeting with directors",
            "days": 1,
            "status": "Not started",
            "log": "",
            "depends_on": [1],
        },
    ]


LOCK_WAIT_SEC = 30
LOCK_POLL_SEC = 0.05
READ_RETRIES = 5


@contextmanager
def _file_lock(path: str):
    """Exclusive lock so API and scripts never read/write the JSON concurrently."""
    lock_path = f"{path}.lock"
    deadline = time.monotonic() + LOCK_WAIT_SEC
    while time.monotonic() < deadline:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(LOCK_POLL_SEC)
    else:
        raise TimeoutError(f"Timed out waiting for lock on {path}")
    try:
        yield
    finally:
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass


def _read_json_locked(path: str) -> dict:
    last_err: Exception | None = None
    for attempt in range(READ_RETRIES):
        try:
            with _file_lock(path):
                with open(path, "r", encoding="utf-8") as f:
                    raw = f.read()
            if not raw.strip():
                raise ValueError(f"Tasks file is empty: {path}")
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            last_err = exc
            if attempt + 1 < READ_RETRIES:
                time.sleep(0.1 * (attempt + 1))
    assert last_err is not None
    raise last_err


def _atomic_write_json(path: str, payload: dict) -> None:
    """Write JSON atomically so readers never see a truncated file."""
    with _file_lock(path):
        dir_name = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


def load_raw(project_id: str = DEFAULT_PROJECT_ID) -> Tuple[str, int, List[Dict]]:
    project_id = resolve_project_id(project_id)
    ensure_data_dir()
    path = _tasks_path(project_id)

    if not os.path.exists(path):
        default_tasks = [] if project_id == "training" else _default_tasks()
        save_raw(project_id, DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks)
        return DEFAULT_PROJECT_START, DEFAULT_GAP_DAYS, default_tasks

    data = _read_json_locked(path)
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
    _atomic_write_json(path, payload)
    invalidate_schedule_cache(project_id)


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
