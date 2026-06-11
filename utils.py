from datetime import datetime, timedelta
from typing import List, Dict

# Your raw working hours per day (total work day)
RAW_DAILY_HOURS = {
    "Monday": 5,
    "Tuesday": 7.5,
    "Wednesday": 7.5,
    "Thursday": 7.5,
    "Friday": 0,
    "Saturday": 0,
    "Sunday": 0,
}

DAILY_PROJECT_HOURS = {day: hours / 2 for day, hours in RAW_DAILY_HOURS.items()}


class SchedulingError(ValueError):
    pass


def add_working_hours(start_date: datetime, hours: float) -> datetime:
    """Add hours (project time) to start_date respecting daily limits."""
    if hours <= 0:
        return start_date
    remaining = hours
    current = start_date
    while remaining > 0:
        weekday = current.strftime("%A")
        available = DAILY_PROJECT_HOURS.get(weekday, 0)
        if available > 0:
            if remaining <= available:
                return current
            remaining -= available
        current += timedelta(days=1)
    return current


def _topological_order(task_ids: List[int], deps: Dict[int, List[int]]) -> List[int]:
    """Kahn's algorithm; raises SchedulingError on cycles or missing ids."""
    in_degree = {tid: 0 for tid in task_ids}
    for tid in task_ids:
        for pred in deps.get(tid, []):
            if pred not in in_degree:
                raise SchedulingError(f"Task {tid} depends on unknown task {pred}")
            in_degree[tid] += 1

    queue = [tid for tid in task_ids if in_degree[tid] == 0]
    order = []
    while queue:
        queue.sort()
        tid = queue.pop(0)
        order.append(tid)
        for other in task_ids:
            if tid in deps.get(other, []):
                in_degree[other] -= 1
                if in_degree[other] == 0:
                    queue.append(other)

    if len(order) != len(task_ids):
        raise SchedulingError("Circular dependency detected between tasks")
    return order


def schedule_tasks(
    tasks: List[Dict], project_start: str, gap_days: int = 1
) -> List[Dict]:
    """
    Schedule from a dependency graph.
    - Empty depends_on: can start at project_start (parallel with other roots).
    - Non-empty: starts after all predecessors end (+ gap_days).
    """
    if not tasks:
        return []

    task_by_id = {t["id"]: t for t in tasks}
    task_ids = list(task_by_id.keys())
    deps = {tid: list(task_by_id[tid].get("depends_on") or []) for tid in task_ids}

    order = _topological_order(task_ids, deps)
    project_dt = datetime.fromisoformat(project_start)
    ends: Dict[int, datetime] = {}
    scheduled = []

    for tid in order:
        t = task_by_id[tid]
        pred_ids = deps[tid]
        if pred_ids:
            earliest = max(ends[p] + timedelta(days=gap_days) for p in pred_ids)
        else:
            earliest = project_dt

        fixed = t.get("fixed_start")
        if fixed:
            fixed_dt = datetime.fromisoformat(fixed)
            start = max(earliest, fixed_dt)
        else:
            start = earliest

        completed_on = t.get("completed_on")
        if t.get("status") == "Completed" and completed_on:
            # Task is actually done: its real end is the completion date,
            # so successors can be scheduled from there instead of the plan.
            end = datetime.fromisoformat(completed_on)
            if end < start:
                start = end
        else:
            effective_hours = float(t["hours"]) + float(t.get("delay_hours") or 0)
            end = add_working_hours(start, effective_hours)
        ends[tid] = end

        task = {k: v for k, v in t.items() if k not in ("start", "end")}
        task["start"] = start.date().isoformat()
        task["end"] = end.isoformat()
        scheduled.append(task)

    return sorted(scheduled, key=lambda x: x["id"])
