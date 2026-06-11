from datetime import datetime

from data_manager import add_log_entry, load_raw, save_tasks
from exceptions import BadRequestError, NotFoundError
from schemas import DelayRequest, LogRequest, TaskCreate, TaskUpdate
from services.project_service import _schedule


def _project_end(tasks) -> str:
    end = max((t["end"] for t in tasks), default="")
    return end[:10] if end else ""


def _optional_str(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _apply_training_fields(task: dict, body) -> None:
    for field in ("department", "subject", "assignee"):
        val = _optional_str(getattr(body, field, None))
        if val:
            task[field] = val


def _apply_training_updates(task: dict, update: TaskUpdate, fields_set: set) -> None:
    for field in ("department", "subject", "assignee"):
        if field in fields_set:
            val = _optional_str(getattr(update, field))
            if val:
                task[field] = val
            else:
                task.pop(field, None)


def create_task(project_id: str, body: TaskCreate):
    project_start, gap_days, tasks = load_raw(project_id)
    new_id = max((t["id"] for t in tasks), default=0) + 1
    for dep_id in body.depends_on:
        if not any(t["id"] == dep_id for t in tasks):
            raise BadRequestError(f"Unknown dependency task {dep_id}")

    new_task = {
        "id": new_id,
        "task": body.task.strip(),
        "hours": body.hours,
        "status": body.status,
        "log": "",
        "depends_on": list(body.depends_on),
    }
    _apply_training_fields(new_task, body)
    tasks.append(new_task)
    save_tasks(project_id, project_start, gap_days, tasks)
    add_log_entry(project_id, f"Created task {new_id}: {body.task.strip()}")
    _, _, scheduled = _schedule(project_id)
    created = next(t for t in scheduled if t["id"] == new_id)
    return {"message": "created", "task": created, "tasks": scheduled}


def update_task(project_id: str, task_id: int, update: TaskUpdate):
    project_start, gap_days, tasks = load_raw(project_id)
    found = False
    for t in tasks:
        if t["id"] == task_id:
            fields_set = update.model_dump(exclude_unset=True)
            previous_status = t.get("status")
            if update.task is not None:
                name = update.task.strip()
                if not name:
                    raise BadRequestError("Task name cannot be empty")
                t["task"] = name
            if update.hours is not None:
                t["hours"] = update.hours
            if update.status is not None:
                t["status"] = update.status
                # Workflow rule: when a task is first moved to In progress,
                # anchor its fixed start to today so end date is recalculated.
                if (
                    update.status == "In progress"
                    and previous_status != "In progress"
                    and "fixed_start" not in fields_set
                ):
                    t["fixed_start"] = datetime.now().date().isoformat()
                # Stamp actual completion date so the scheduler can use it as
                # the task's real end; clear it if the task is reopened.
                if update.status == "Completed" and previous_status != "Completed":
                    t["completed_on"] = datetime.now().date().isoformat()
                elif update.status != "Completed":
                    t.pop("completed_on", None)
            if update.log is not None:
                t["log"] = update.log
            if update.depends_on is not None:
                t["depends_on"] = update.depends_on
            if "fixed_start" in fields_set:
                if update.fixed_start:
                    t["fixed_start"] = update.fixed_start
                else:
                    t.pop("fixed_start", None)
            _apply_training_updates(t, update, fields_set)
            found = True
            break
    if not found:
        raise NotFoundError("Task not found")

    save_tasks(project_id, project_start, gap_days, tasks)
    add_log_entry(
        project_id,
        f"Updated task {task_id}: {update.model_dump(exclude_unset=True)}",
    )
    _, _, scheduled = _schedule(project_id)
    return {
        "message": "updated",
        "tasks": scheduled,
        "project_end": _project_end(scheduled),
    }


def delete_task(project_id: str, task_id: int):
    project_start, gap_days, tasks = load_raw(project_id)
    removed = None
    for t in tasks:
        if t["id"] == task_id:
            removed = t
            break
    if not removed:
        raise NotFoundError("Task not found")

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

    save_tasks(project_id, project_start, gap_days, tasks)
    add_log_entry(project_id, f"Deleted task {task_id}: {removed.get('task', '')}")
    _, _, scheduled = _schedule(project_id)
    return {
        "message": "deleted",
        "tasks": scheduled,
        "project_end": _project_end(scheduled),
        "dependents_updated": dependents,
    }


def append_task_log(project_id: str, task_id: int, body: LogRequest):
    project_start, gap_days, tasks = load_raw(project_id)
    for t in tasks:
        if t["id"] == task_id:
            stamp = datetime.now().isoformat(timespec="seconds")
            line = f"{stamp} - {body.message}\n"
            t["log"] = (t.get("log") or "") + line
            save_tasks(project_id, project_start, gap_days, tasks)
            add_log_entry(
                project_id,
                f"Task {task_id} ({t.get('task', '')}): {body.message}",
            )
            _, _, scheduled = _schedule(project_id)
            updated = next(x for x in scheduled if x["id"] == task_id)
            return {"message": "logged", "task": updated}
    raise NotFoundError("Task not found")


def log_task_delay(project_id: str, task_id: int, body: DelayRequest):
    if body.hours <= 0:
        raise BadRequestError("Delay hours must be greater than zero")
    reason = body.reason.strip()
    if not reason:
        raise BadRequestError("Delay reason is required")

    project_start, gap_days, tasks = load_raw(project_id)
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
        raise NotFoundError("Task not found")

    save_tasks(project_id, project_start, gap_days, tasks)
    add_log_entry(
        project_id,
        f"Task {task_id} delay +{body.hours}h: {reason} "
        f"(total delay on task: {found_task.get('delay_hours')}h)",
    )
    _, _, scheduled = _schedule(project_id)
    updated = next(x for x in scheduled if x["id"] == task_id)
    return {
        "message": "delay logged",
        "task": updated,
        "tasks": scheduled,
        "project_end": _project_end(scheduled),
    }
