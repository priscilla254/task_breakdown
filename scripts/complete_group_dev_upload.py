"""Complete dev+upload (and any missing content) for Group modules with step 1.5 done."""
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_manager import _atomic_write_json, _read_json_locked
from duration import parse_task_days
from utils import add_working_hours

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks-training.json"
CONTENT_STEPS = ("1.1", "1.2", "1.3", "1.4", "1.5")
DEV_UPLOAD_STEPS = (
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
    "3.1", "3.2", "3.3",
)


def _step_order(step_id: str) -> tuple:
    parts = step_id.split(".")
    return (int(parts[0]), int(parts[1]))


def _planned_end(start_iso: str, days: float) -> str:
    start = datetime.fromisoformat(start_iso[:10])
    hours = parse_task_days(days) * 7.5
    end = add_working_hours(start, hours) if hours > 0 else start
    return end.date().isoformat()


def main():
    data = _read_json_locked(str(DATA_PATH))

    by_module = defaultdict(list)
    for t in data["tasks"]:
        if t.get("department") == "Group" and t.get("module_index") is not None:
            by_module[t["module_index"]].append(t)

    target_modules = []
    for mi, mod_tasks in by_module.items():
        steps = {t["step_id"]: t for t in mod_tasks}
        if steps.get("1.5", {}).get("status") == "Completed":
            target_modules.append(mi)

    updated = []
    for mi in sorted(target_modules):
        mod_tasks = sorted(by_module[mi], key=lambda t: _step_order(t["step_id"]))
        steps = {t["step_id"]: t for t in mod_tasks}
        anchor = steps["1.5"].get("completed_on") or "2026-06-16"
        # Fill any content steps not yet marked (e.g. M6 missing 1.1–1.3)
        cursor = anchor
        for sid in CONTENT_STEPS:
            t = steps[sid]
            if t.get("status") != "Completed":
                t["status"] = "Completed"
                t["completed_on"] = cursor
                updated.append((mi, sid, "content-fill", cursor))
            else:
                cursor = t.get("completed_on") or cursor

        # Dev + upload: chain completed_on from 1.5 end through dependency order
        end_15 = steps["1.5"].get("completed_on") or anchor
        ends = {"1.5": datetime.fromisoformat(end_15[:10])}
        for t in mod_tasks:
            if t["step_id"] not in DEV_UPLOAD_STEPS:
                continue
            if t.get("status") == "Completed":
                co = t.get("completed_on")
                if co:
                    ends[t["step_id"]] = datetime.fromisoformat(co[:10])
                continue
            preds = t.get("depends_on") or []
            if preds:
                pred_ends = []
                for p in preds:
                    for x in mod_tasks:
                        if x["id"] == p:
                            pe = ends.get(x["step_id"], datetime.fromisoformat(end_15[:10]))
                            pred_ends.append(pe)
                start_dt = max(pred_ends) if pred_ends else datetime.fromisoformat(end_15[:10])
            else:
                start_dt = datetime.fromisoformat(end_15[:10])
            completed = _planned_end(start_dt.isoformat(), t.get("days", 1))
            t["status"] = "Completed"
            t["completed_on"] = completed
            ends[t["step_id"]] = datetime.fromisoformat(completed)
            updated.append((mi, t["step_id"], "dev/upload", completed))

    _atomic_write_json(str(DATA_PATH), data)

    print(f"Modules with 1.5 complete: {target_modules}")
    print(f"Updated {len(updated)} tasks")
    for row in updated:
        print(f"  M{row[0]} {row[1]} ({row[2]}) -> {row[3]}")


if __name__ == "__main__":
    main()
