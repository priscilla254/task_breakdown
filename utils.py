from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

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
# Monday=0 … Sunday=6 — avoids strftime in the hot loop
_WEEKDAY_HOURS = tuple(
    DAILY_PROJECT_HOURS[d]
    for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
)


class SchedulingError(ValueError):
    pass


def add_working_hours(start_date: datetime, hours: float) -> datetime:
    """Add hours (project time) to start_date respecting daily limits."""
    if hours <= 0:
        return start_date
    remaining = hours
    current = start_date
    while remaining > 0:
        available = _WEEKDAY_HOURS[current.weekday()]
        if available > 0:
            if remaining <= available:
                return current
            remaining -= available
        current += timedelta(days=1)
    return current


def subtract_working_hours(end_date: datetime, hours: float) -> datetime:
    """Subtract project hours from end_date (walk backward over working days)."""
    if hours <= 0:
        return end_date
    remaining = hours
    current = end_date
    while remaining > 0:
        available = _WEEKDAY_HOURS[current.weekday()]
        if available > 0:
            if remaining <= available:
                return current
            remaining -= available
        current -= timedelta(days=1)
    return current


def _resolve_task_span(raw: Dict, earliest: datetime) -> tuple:
    """
    Compute (start, end) for one task.
    Completed tasks use completed_on as truth; pipeline earliest is a floor only
    when the completion fits after that slot.
    """
    completed_on = raw.get("completed_on")
    if raw.get("status") == "Completed" and completed_on:
        end_dt = datetime.fromisoformat(str(completed_on)[:10])
        task_days = parse_task_days(raw.get("days", 0))
        if task_days == 0:
            start_dt = end_dt
        else:
            start_dt = subtract_working_hours(
                end_dt, days_to_scheduler_hours(task_days)
            )
        if earliest <= end_dt:
            start_dt = max(start_dt, earliest)
        if start_dt > end_dt:
            start_dt = end_dt
        return start_dt, end_dt

    start_dt = earliest
    fixed = raw.get("fixed_start")
    if fixed:
        start_dt = max(start_dt, datetime.fromisoformat(str(fixed)[:10]))

    task_days = parse_task_days(raw.get("days", 1))
    delay_days_total = int(raw.get("delay_days") or 0)
    fixed_end = raw.get("fixed_end")
    if fixed_end:
        end_dt = datetime.fromisoformat(str(fixed_end)[:10])
        return start_dt, end_dt if end_dt >= start_dt else start_dt
    if task_days == 0:
        return start_dt, start_dt
    effective_hours = days_to_scheduler_hours(task_days)
    if delay_days_total > 0:
        effective_hours += days_to_scheduler_hours(delay_days_total)
    return start_dt, add_working_hours(start_dt, effective_hours)


def _end_from_task_days(raw: Dict, start_dt: datetime) -> datetime:
    """Backward-compatible end helper; prefer _resolve_task_span for new logic."""
    _, end_dt = _resolve_task_span(raw, start_dt)
    return end_dt


def _topological_order(task_ids: List[int], deps: Dict[int, List[int]]) -> List[int]:
    """Kahn's algorithm; raises SchedulingError on cycles or missing ids."""
    in_degree = {tid: 0 for tid in task_ids}
    successors: Dict[int, List[int]] = defaultdict(list)

    for tid in task_ids:
        for pred in deps.get(tid, []):
            if pred not in in_degree:
                raise SchedulingError(f"Task {tid} depends on unknown task {pred}")
            in_degree[tid] += 1
            successors[pred].append(tid)

    queue = [tid for tid in task_ids if in_degree[tid] == 0]
    order = []
    while queue:
        queue.sort()
        tid = queue.pop(0)
        order.append(tid)
        for other in successors.get(tid, ()):
            in_degree[other] -= 1
            if in_degree[other] == 0:
                queue.append(other)

    if len(order) != len(task_ids):
        raise SchedulingError("Circular dependency detected between tasks")
    return order


def _task_start_dt(item: Dict) -> datetime:
    return datetime.fromisoformat(item["start"][:10])


def _task_end_dt(item: Dict) -> datetime:
    return datetime.fromisoformat(str(item["end"])[:10])


def _start_align_ref(raw: Dict) -> Optional[int]:
    ref = raw.get("starts_when_start_of")
    if ref is None:
        ref = raw.get("starts_with")
    return ref


def _align_parallel_group(
    pg_key: str,
    by_parallel: Dict[str, List[Dict]],
    task_by_id: Dict[int, Dict],
    ends: Dict[int, datetime],
) -> bool:
    """Align parallel group members to a shared block; return True if any span changed."""
    members = by_parallel[pg_key]
    if all(
        task_by_id[m["id"]].get("status") == "Completed"
        and task_by_id[m["id"]].get("completed_on")
        for m in members
    ):
        return False

    start_dt = max(_task_start_dt(m) for m in members)
    raw_days = [parse_task_days(task_by_id[m["id"]].get("days", 1)) for m in members]
    block_days = max(raw_days) if len(members) > 1 else raw_days[0]
    end_dt = (
        add_working_hours(start_dt, days_to_scheduler_hours(block_days))
        if block_days > 0
        else start_dt
    )
    start_iso = start_dt.date().isoformat()
    end_iso = end_dt.isoformat()
    changed = False
    for m in members:
        if m.get("start") != start_iso or m.get("end") != end_iso:
            changed = True
        m["start"] = start_iso
        m["end"] = end_iso
        ends[m["id"]] = end_dt
    return changed


def _apply_parallel_groups(
    by_parallel: Dict[str, List[Dict]],
    task_by_id: Dict[int, Dict],
    ends: Dict[int, datetime],
) -> bool:
    changed = False
    for pg_key in by_parallel:
        if _align_parallel_group(pg_key, by_parallel, task_by_id, ends):
            changed = True
    return changed


def _uses_module_scheduling(tasks: List[Dict]) -> bool:
    """Training tasks are grouped into modules with no cross-module depends_on."""
    if not tasks:
        return False
    return all(t.get("module_index") is not None for t in tasks)


def _schedule_task_graph(
    tasks: List[Dict],
    project_start: str,
    gap_days: int,
    external_ends: Optional[Dict[int, datetime]] = None,
    external_scheduled: Optional[Dict[int, Dict]] = None,
) -> List[Dict]:
    """
    Schedule one task graph (a single module or the full project).
    external_* supplies cross-module predecessor ends / start-align refs.
    """
    if not tasks:
        return []

    external_ends = external_ends or {}
    external_scheduled = external_scheduled or {}

    task_by_id = {t["id"]: t for t in tasks}
    task_ids = list(task_by_id.keys())
    deps = {tid: list(task_by_id[tid].get("depends_on") or []) for tid in task_ids}

    order = _topological_order(task_ids, deps)
    project_dt = datetime.fromisoformat(project_start)
    ends: Dict[int, datetime] = {}
    scheduled = []

    def _pred_end(pred_id: int) -> datetime:
        if pred_id in ends:
            return ends[pred_id]
        if pred_id in external_ends:
            return external_ends[pred_id]
        raise SchedulingError(f"Task depends on unknown predecessor {pred_id}")

    def _ref_start(ref_id: int, id_to_scheduled: Dict[int, Dict]) -> datetime:
        ref = id_to_scheduled.get(ref_id)
        if ref is not None:
            return _task_start_dt(ref)
        ext = external_scheduled.get(ref_id)
        if ext is not None:
            return _task_start_dt(ext)
        raise SchedulingError(f"Start-align unknown task {ref_id}")

    for tid in order:
        t = task_by_id[tid]
        pred_ids = deps[tid]
        if pred_ids:
            earliest = max(_pred_end(p) + timedelta(days=gap_days) for p in pred_ids)
        else:
            earliest = project_dt

        fixed = t.get("fixed_start")
        if fixed:
            fixed_dt = datetime.fromisoformat(str(fixed)[:10])
            start = max(earliest, fixed_dt)
        else:
            start = earliest

        start, end = _resolve_task_span(t, start)
        ends[tid] = end

        task = {k: v for k, v in t.items() if k not in ("start", "end")}
        task["start"] = start.date().isoformat()
        task["end"] = end.isoformat()
        scheduled.append(task)

    id_to_scheduled = {t["id"]: t for t in scheduled}

    by_parallel: Dict[str, List[Dict]] = defaultdict(list)
    for t in scheduled:
        pg = task_by_id[t["id"]].get("parallel_group")
        if pg:
            by_parallel[pg].append(t)

    pinned_ids: Set[int] = {
        t["id"] for t in scheduled if task_by_id[t["id"]].get("ends_with") is not None
    }

    def _propagate_task(tid: int) -> bool:
        raw = task_by_id[tid]
        t = id_to_scheduled[tid]
        pred_ids = deps[tid]
        if pred_ids:
            earliest = max(_pred_end(p) + timedelta(days=gap_days) for p in pred_ids)
        else:
            earliest = project_dt

        fixed = raw.get("fixed_start")
        if fixed:
            earliest = max(earliest, datetime.fromisoformat(str(fixed)[:10]))

        align_ref = _start_align_ref(raw)
        if align_ref is not None:
            earliest = max(earliest, _ref_start(align_ref, id_to_scheduled))

        start_dt, end_dt = _resolve_task_span(raw, earliest)
        if end_dt < start_dt:
            end_dt = start_dt

        prev_start = t["start"]
        prev_end = t["end"]
        t["start"] = start_dt.date().isoformat()
        t["end"] = end_dt.isoformat()
        ends[tid] = end_dt
        return t["start"] != prev_start or t["end"] != prev_end

    max_sweeps = len(order) * 2 + 2
    changed = True
    for _ in range(max_sweeps):
        if not changed:
            break
        changed = False
        for tid in order:
            if tid in pinned_ids:
                continue
            if _propagate_task(tid):
                changed = True
        if _apply_parallel_groups(by_parallel, task_by_id, ends):
            changed = True

    for tid in pinned_ids:
        t = id_to_scheduled[tid]
        raw = task_by_id[tid]
        pred_ids = deps[tid]
        if pred_ids:
            earliest = max(_pred_end(p) + timedelta(days=gap_days) for p in pred_ids)
        else:
            earliest = project_dt

        start_dt = _task_start_dt(t)
        starts_with = raw.get("starts_with")
        if starts_with is not None:
            start_dt = _ref_start(starts_with, id_to_scheduled)

        fixed = raw.get("fixed_start")
        if fixed:
            earliest = max(earliest, datetime.fromisoformat(str(fixed)[:10]))
        start_dt = max(start_dt, earliest)

        end_dt = _task_end_dt(t)
        ends_with = raw.get("ends_with")
        if ends_with is not None:
            end_dt = _pred_end(ends_with)

        if end_dt < start_dt:
            raise SchedulingError(
                f"Task {tid}: end before start after final re-alignment"
            )

        t["start"] = start_dt.date().isoformat()
        t["end"] = end_dt.isoformat()
        ends[tid] = end_dt

    return scheduled


def _schedule_by_modules(
    tasks: List[Dict], project_start: str, gap_days: int
) -> List[Dict]:
    """Schedule training modules in order; only ~16 tasks propagate per module."""
    by_module: Dict[int, List[Dict]] = defaultdict(list)
    for t in tasks:
        by_module[int(t["module_index"])].append(t)

    external_ends: Dict[int, datetime] = {}
    external_scheduled: Dict[int, Dict] = {}
    all_scheduled: List[Dict] = []

    for module_index in sorted(by_module.keys()):
        mod_scheduled = _schedule_task_graph(
            by_module[module_index],
            project_start,
            gap_days,
            external_ends=external_ends,
            external_scheduled=external_scheduled,
        )
        for t in mod_scheduled:
            external_ends[t["id"]] = _task_end_dt(t)
            external_scheduled[t["id"]] = t
        all_scheduled.extend(mod_scheduled)

    return sorted(all_scheduled, key=lambda x: x["id"])


def schedule_tasks(
    tasks: List[Dict], project_start: str, gap_days: int = 1
) -> List[Dict]:
    """
    Schedule from a dependency graph.
    - Training (module_index on every task): per-module scheduling in module order.
    - Other projects: full-graph scheduling.
    """
    if _uses_module_scheduling(tasks):
        return _schedule_by_modules(tasks, project_start, gap_days)
    return _schedule_task_graph(tasks, project_start, gap_days)
