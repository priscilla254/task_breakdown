import os

from data_manager import (
    DEFAULT_PROJECT_ID,
    add_log_entry,
    list_projects,
    load_raw,
    load_tasks,
    resolve_project_id,
    save_tasks,
    shift_project_start,
    _tasks_path,
)
from exceptions import BadRequestError
from schedule_cache import get_cached, put_cached
from utils import SchedulingError


def _tasks_file_mtime(project_id: str) -> float:
    path = _tasks_path(project_id)
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


def _schedule(project_id: str):
    pid = resolve_project_id(project_id)
    mtime = _tasks_file_mtime(pid)
    cached = get_cached(pid, mtime)
    if cached is not None:
        return cached
    try:
        project_start, gap_days, tasks = load_tasks(pid)
    except SchedulingError as e:
        raise BadRequestError(str(e)) from e
    put_cached(pid, project_start, gap_days, tasks, mtime)
    return project_start, gap_days, tasks


def get_projects_payload():
    return {"projects": list_projects(), "default": DEFAULT_PROJECT_ID}


def get_tasks_payload(project_id: str):
    project_start, gap_days, tasks = _schedule(project_id)
    return {
        "project": project_id,
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": tasks,
    }


def update_project_start(project_id: str, project_start: str):
    _, gap_days, tasks = load_raw(project_id)
    save_tasks(project_id, project_start, gap_days, tasks)
    add_log_entry(project_id, f"Project start set to {project_start}")
    _, _, scheduled = _schedule(project_id)
    return {
        "project": project_id,
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": scheduled,
    }


def shift_timeline(project_id: str, extra_days: int):
    new_start = shift_project_start(project_id, extra_days)
    add_log_entry(
        project_id,
        f"Shifted project start by {extra_days} days to {new_start}",
    )
    project_start, _, tasks = _schedule(project_id)
    return {
        "message": f"Shifted project by {extra_days} days",
        "project_start": project_start,
        "tasks": tasks,
    }
