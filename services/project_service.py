from data_manager import (
    DEFAULT_PROJECT_ID,
    add_log_entry,
    list_projects,
    load_raw,
    load_tasks,
    save_tasks,
    shift_project_start,
)
from exceptions import BadRequestError
from utils import SchedulingError


def _schedule(project_id: str):
    try:
        return load_tasks(project_id)
    except SchedulingError as e:
        raise BadRequestError(str(e)) from e


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
