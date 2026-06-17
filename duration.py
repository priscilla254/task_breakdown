"""Task duration: UI/storage uses work days; scheduler uses project hours."""

import math

HOURS_PER_WORK_DAY = 7.5


def parse_task_days(value) -> float:
    """Parse stored days; allows 0 (milestone) and fractional values (e.g. 0.5)."""
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 1.0


def normalize_days(value) -> int:
    """Whole work days for legacy display paths (minimum 1)."""
    return max(1, math.ceil(parse_task_days(value)))


def hours_to_days(hours: float) -> int:
    """Convert legacy project hours to work days (ceil, minimum 1)."""
    if hours is None or float(hours) <= 0:
        return 1
    return max(1, math.ceil(float(hours) / HOURS_PER_WORK_DAY))


def days_to_scheduler_hours(days) -> float:
    """Work days → hours consumed by the scheduling calendar."""
    return parse_task_days(days) * HOURS_PER_WORK_DAY
