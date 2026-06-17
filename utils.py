from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set

from duration import days_to_scheduler_hours, parse_task_days

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


def _end_from_task_days(raw: Dict, start_dt: datetime) -> datetime:
    completed_on = raw.get("completed_on")
    if raw.get("status") == "Completed" and completed_on:
        end_dt = datetime.fromisoformat(completed_on)
        return end_dt if end_dt >= start_dt else start_dt
    task_days = parse_task_days(raw.get("days", 1))
    delay_days_total = int(raw.get("delay_days") or 0)
    fixed_end = raw.get("fixed_end")
    if fixed_end:
        end_dt = datetime.fromisoformat(str(fixed_end)[:10])
        return end_dt if end_dt >= start_dt else start_dt
    if task_days == 0:
        return start_dt
    effective_hours = days_to_scheduler_hours(task_days)
    if delay_days_total > 0:
        effective_hours += days_to_scheduler_hours(delay_days_total)
    return add_working_hours(start_dt, effective_hours)


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
            end = datetime.fromisoformat(completed_on)
            if end < start:
                start = end
        else:
            end = _end_from_task_days(t, start)
        ends[tid] = end

        task = {k: v for k, v in t.items() if k not in ("start", "end")}
        task["start"] = start.date().isoformat()
        task["end"] = end.isoformat()
        scheduled.append(task)

    id_to_scheduled = {t["id"]: t for t in scheduled}

    def _task_start_dt(item: Dict) -> datetime:
        return datetime.fromisoformat(item["start"][:10])

    def _task_end_dt(item: Dict) -> datetime:
        return datetime.fromisoformat(str(item["end"])[:10])

    def _recompute_task_span(t: Dict, raw: Dict, earliest: datetime) -> None:
        start_dt = max(_task_start_dt(t), earliest)
        end_dt = _end_from_task_days(raw, start_dt)
        if end_dt < start_dt:
            end_dt = start_dt
        t["start"] = start_dt.date().isoformat()
        t["end"] = end_dt.isoformat()
        ends[t["id"]] = end_dt

    by_parallel: Dict[str, List] = defaultdict(list)
    for t in scheduled:
        pg = task_by_id[t["id"]].get("parallel_group")
        if pg:
            by_parallel[pg].append(t)

    def _apply_parallel_groups() -> None:
        """Align all members of each parallel group to share start/end."""
        for members in by_parallel.values():
            start_dt = max(_task_start_dt(m) for m in members)
            raw_days = [parse_task_days(task_by_id[m["id"]].get("days", 1)) for m in members]
            block_days = max(raw_days) if len(members) > 1 else raw_days[0]
            end_dt = add_working_hours(start_dt, days_to_scheduler_hours(block_days)) if block_days > 0 else start_dt
            for m in members:
                m["start"] = start_dt.date().isoformat()
                m["end"] = end_dt.isoformat()
                ends[m["id"]] = end_dt

    # Only tasks with ends_with are fully pinned; starts_with / starts_when_start_of
    # are re-evaluated each propagation sweep so module chains can cascade.
    pinned_ids: Set[int] = {
        t["id"] for t in scheduled if task_by_id[t["id"]].get("ends_with") is not None
    }

    def _start_align_ref(raw: Dict):
        return raw.get("starts_when_start_of") or raw.get("starts_with")

    # Main propagation: iterates until stable, respecting rolling start triggers
    # (starts_when_start_of / starts_with) and parallel groups each sweep.
    changed = True
    for _ in range(len(order) * 2 + 2):
        if not changed:
            break
        changed = False
        for tid in order:
            raw = task_by_id[tid]
            if tid in pinned_ids:
                continue
            t = id_to_scheduled[tid]
            pred_ids = deps[tid]
            if pred_ids:
                earliest = max(ends[p] + timedelta(days=gap_days) for p in pred_ids)
            else:
                earliest = project_dt

            fixed = raw.get("fixed_start")
            if fixed:
                earliest = max(earliest, datetime.fromisoformat(fixed[:10]))

            align_ref = _start_align_ref(raw)
            if align_ref is not None:
                ref = id_to_scheduled.get(align_ref)
                if ref is None:
                    raise SchedulingError(
                        f"Task {tid} start-align unknown task {align_ref}"
                    )
                earliest = max(earliest, _task_start_dt(ref))

            start_dt = max(_task_start_dt(t), earliest)
            end_dt = _end_from_task_days(raw, start_dt)
            if end_dt < start_dt:
                end_dt = start_dt

            prev_start = t["start"]
            prev_end = t["end"]
            t["start"] = start_dt.date().isoformat()
            t["end"] = end_dt.isoformat()
            ends[tid] = end_dt
            if t["start"] != prev_start or t["end"] != prev_end:
                changed = True

        # Re-align parallel groups after each propagation sweep.
        _apply_parallel_groups()

    # Final phase: re-align pinned tasks with settled ends.
    for tid in pinned_ids:
        t = id_to_scheduled[tid]
        raw = task_by_id[tid]
        pred_ids = deps[tid]
        if pred_ids:
            earliest = max(ends[p] + timedelta(days=gap_days) for p in pred_ids)
        else:
            earliest = project_dt

        start_dt = _task_start_dt(t)
        starts_with = raw.get("starts_with")
        if starts_with is not None:
            ref = id_to_scheduled.get(starts_with)
            if ref is None:
                raise SchedulingError(f"Task {tid} starts_with unknown task {starts_with}")
            start_dt = _task_start_dt(ref)

        fixed = raw.get("fixed_start")
        if fixed:
            earliest = max(earliest, datetime.fromisoformat(fixed[:10]))
        start_dt = max(start_dt, earliest)

        end_dt = _task_end_dt(t)
        ends_with = raw.get("ends_with")
        if ends_with is not None:
            if ends_with not in ends:
                raise SchedulingError(f"Task {tid} ends_with unknown task {ends_with}")
            end_dt = ends[ends_with]

        if end_dt < start_dt:
            raise SchedulingError(
                f"Task {tid}: end before start after final re-alignment"
            )

        t["start"] = start_dt.date().isoformat()
        t["end"] = end_dt.isoformat()
        ends[tid] = end_dt

    return sorted(scheduled, key=lambda x: x["id"])
