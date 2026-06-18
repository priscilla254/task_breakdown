"""In-memory cache of scheduled task lists (per project)."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# project_id -> cached payload
_cache: Dict[str, dict] = {}

ScheduleResult = Tuple[str, int, List[dict]]


def get_cached(project_id: str, file_mtime: float) -> Optional[ScheduleResult]:
    entry = _cache.get(project_id)
    if entry is None:
        return None
    if entry["mtime"] != file_mtime:
        _cache.pop(project_id, None)
        return None
    return entry["project_start"], entry["gap_days"], entry["tasks"]


def put_cached(
    project_id: str,
    project_start: str,
    gap_days: int,
    tasks: List[dict],
    file_mtime: float,
) -> None:
    _cache[project_id] = {
        "project_start": project_start,
        "gap_days": gap_days,
        "tasks": tasks,
        "mtime": file_mtime,
    }


def invalidate_schedule_cache(project_id: str) -> None:
    _cache.pop(project_id, None)


def clear_schedule_cache() -> None:
    _cache.clear()
