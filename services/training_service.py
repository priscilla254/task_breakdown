"""Training platform: module summaries and scoped task loads."""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from exceptions import BadRequestError
from services.project_service import _schedule
from utils import _uses_module_scheduling


def _module_name_from_task(task: str) -> str:
    sep = (task or "").find(" - ")
    return task[:sep] if sep >= 0 else (task or "")


def _to_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def build_module_summaries(tasks: List[Dict]) -> List[Dict]:
    """One row per module: span from earliest start to latest end."""
    by_module: Dict[int, Dict] = {}
    for t in tasks:
        mi = t.get("module_index")
        if mi is None:
            continue
        row = by_module.get(mi)
        if row is None:
            row = {
                "module_index": mi,
                "module_name": _module_name_from_task(t.get("task", "")),
                "department": t.get("department") or "",
                "subject": t.get("subject") or "",
                "start": t.get("start"),
                "end": t.get("end"),
                "step_count": 0,
                "representative_task_id": t["id"],
                "_rep_step": t.get("step_id"),
            }
            by_module[mi] = row
        row["step_count"] += 1
        if t.get("start") and (not row["start"] or t["start"] < row["start"]):
            row["start"] = t["start"]
        if t.get("end") and (not row["end"] or t["end"] > row["end"]):
            row["end"] = t["end"]
        if t.get("step_id") == "3.3":
            row["representative_task_id"] = t["id"]
            row["_rep_step"] = "3.3"
        elif t.get("step_id") == "1.1" and row.get("_rep_step") != "3.3":
            row["representative_task_id"] = t["id"]
            row["_rep_step"] = "1.1"

    modules = []
    for mi in sorted(by_module.keys()):
        row = by_module[mi]
        row.pop("_rep_step", None)
        mod_tasks = [t for t in tasks if t.get("module_index") == mi]
        if mod_tasks and all(t.get("status") == "Completed" for t in mod_tasks):
            completed_dates = [
                _to_date(t.get("completed_on"))
                for t in mod_tasks
                if t.get("completed_on")
            ]
            completed_dates = [d for d in completed_dates if d]
            if completed_dates:
                row["start"] = min(completed_dates).date().isoformat()
                row["end"] = max(completed_dates).date().isoformat()
                row["all_completed"] = True
        start_dt = _to_date(row.get("start"))
        end_dt = _to_date(row.get("end"))
        if start_dt and end_dt:
            span_days = max(1, (end_dt - start_dt).days + 1)
        else:
            span_days = 0
        modules.append(
            {
                **row,
                "span_days": span_days,
                "label": f"M{mi} · {row['module_name']}",
            }
        )
    return modules


def _remaining_days(tasks: List[Dict]) -> float:
    total = 0.0
    for t in tasks:
        if t.get("status") == "Completed":
            continue
        total += float(t.get("days") or 0)
    return total


def build_training_stats(tasks: List[Dict]) -> Dict:
    total_effort = sum(float(t.get("days") or 0) for t in tasks)
    project_end = max((str(t.get("end", ""))[:10] for t in tasks), default="")
    return {
        "total_effort_days": total_effort,
        "remaining_days": _remaining_days(tasks),
        "project_end": project_end,
        "task_count": len(tasks),
    }


def build_filter_options(tasks: List[Dict]) -> Dict:
    departments = sorted({t.get("department") or "" for t in tasks if t.get("department")})
    subjects = sorted({t.get("subject") or "" for t in tasks if t.get("subject")})
    assignees = sorted({t.get("assignee") or "" for t in tasks if t.get("assignee")})
    subjects_by_department: Dict[str, List[str]] = defaultdict(set)
    for t in tasks:
        dept = t.get("department") or ""
        sub = t.get("subject") or ""
        if dept and sub:
            subjects_by_department[dept].add(sub)
    return {
        "departments": departments,
        "subjects": subjects,
        "assignees": assignees,
        "subjects_by_department": {
            dept: sorted(subs) for dept, subs in subjects_by_department.items()
        },
    }


def _require_training_tasks(tasks: List[Dict]) -> None:
    if not _uses_module_scheduling(tasks):
        raise BadRequestError("Module API is only available for the training project")


def get_modules_payload(project_id: str) -> Dict:
    project_start, gap_days, tasks = _schedule(project_id)
    _require_training_tasks(tasks)
    modules = build_module_summaries(tasks)
    return {
        "project": project_id,
        "project_start": project_start,
        "gap_days": gap_days,
        "modules": modules,
        "stats": build_training_stats(tasks),
        "filter_options": build_filter_options(tasks),
        "total_modules": len(modules),
        "total_tasks": len(tasks),
    }


def get_module_tasks_payload(
    project_id: str,
    module_index: Optional[int] = None,
    department: Optional[str] = None,
    subject: Optional[str] = None,
) -> Dict:
    project_start, gap_days, tasks = _schedule(project_id)
    _require_training_tasks(tasks)

    if module_index is not None:
        tasks = [t for t in tasks if t.get("module_index") == module_index]
        if not tasks:
            raise BadRequestError(f"Module {module_index} not found")
    else:
        if department:
            tasks = [t for t in tasks if (t.get("department") or "") == department]
        if subject:
            tasks = [t for t in tasks if (t.get("subject") or "") == subject]

    return {
        "project": project_id,
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": tasks,
        "count": len(tasks),
    }
