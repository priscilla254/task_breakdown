"""One-off migration: hours → days in project JSON files (days only in output)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_manager import _clean_task, save_raw, load_raw

DATA = ROOT / "data"
PROJECTS = ("phase1", "training")


def migrate_project(project_id: str) -> int:
    project_start, gap_days, tasks = load_raw(project_id)
    cleaned = [_clean_task(t) for t in tasks]
    save_raw(project_id, project_start, gap_days, cleaned)
    return len(cleaned)


def main():
    for pid in PROJECTS:
        path = DATA / f"tasks-{pid}.json"
        if not path.exists():
            print(f"skip {pid}: no file")
            continue
        n = migrate_project(pid)
        print(f"migrated {pid}: {n} tasks (days only)")


if __name__ == "__main__":
    main()
