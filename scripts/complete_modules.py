"""Mark all steps (content, development, upload) Completed for given module indices."""
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_manager import _atomic_write_json, _read_json_locked
from duration import parse_task_days
from utils import add_working_hours

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks-training.json"
DEFAULT_ANCHOR = "2026-06-16"


def _step_order(step_id: str) -> tuple:
    parts = step_id.split(".")
    return (int(parts[0]), int(parts[1]))


def _planned_end(start_iso: str, days: float) -> str:
    start = datetime.fromisoformat(start_iso[:10])
    hours = parse_task_days(days) * 7.5
    end = add_working_hours(start, hours) if hours > 0 else start
    return end.date().isoformat()


def _id_to_step(mod_tasks: list) -> dict:
    return {t["id"]: t["step_id"] for t in mod_tasks}


def complete_module(mod_tasks: list, anchor: str = DEFAULT_ANCHOR) -> list:
    """Return list of (step_id, completed_on) for tasks that were updated."""
    mod_tasks = sorted(mod_tasks, key=lambda t: _step_order(t["step_id"]))
    id_step = _id_to_step(mod_tasks)
    ends: dict[str, datetime] = {}
    updated = []

    for t in mod_tasks:
        sid = t["step_id"]
        if t.get("status") == "Completed" and t.get("completed_on"):
            ends[sid] = datetime.fromisoformat(t["completed_on"][:10])
            continue

        preds = t.get("depends_on") or []
        if preds:
            pred_ends = [
                ends.get(id_step[p], datetime.fromisoformat(anchor))
                for p in preds
                if p in id_step
            ]
            start_dt = max(pred_ends) if pred_ends else datetime.fromisoformat(anchor)
        else:
            start_dt = datetime.fromisoformat(anchor)

        completed = _planned_end(start_dt.isoformat(), t.get("days", 0))
        t["status"] = "Completed"
        t["completed_on"] = completed
        ends[sid] = datetime.fromisoformat(completed)
        updated.append((sid, completed))

    return updated


def main(module_indices: list[int]):
    data = _read_json_locked(str(DATA_PATH))
    by_module = defaultdict(list)
    for t in data["tasks"]:
        if t.get("module_index") is not None:
            by_module[t["module_index"]].append(t)

    total = 0
    for mi in sorted(module_indices):
        if mi not in by_module:
            print(f"M{mi}: not found, skipping")
            continue
        rows = complete_module(by_module[mi])
        name = by_module[mi][0]["task"].split(" - ")[0]
        print(f"M{mi} {name}: updated {len(rows)} tasks")
        total += len(rows)

    _atomic_write_json(str(DATA_PATH), data)
    print(f"Done — {total} tasks marked Completed")


if __name__ == "__main__":
    indices = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [5, 6, 7, 8, 9, 10, 11]
    main(indices)
