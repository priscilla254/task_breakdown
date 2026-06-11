"""Build CSV exports of a project's scheduled task list."""

import csv
import io

from services.project_service import _schedule

COLUMNS = [
    "ID",
    "Task",
    "Phase",
    "Department",
    "Subject",
    "Assignee",
    "Hours",
    "Delay hours",
    "Depends on",
    "Start",
    "End",
    "Status",
    "Completed on",
]


def tasks_to_csv(project_id: str) -> str:
    _, _, tasks = _schedule(project_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    for t in tasks:
        writer.writerow(
            [
                t.get("id", ""),
                t.get("task", ""),
                t.get("phase", ""),
                t.get("department", ""),
                t.get("subject", ""),
                t.get("assignee", ""),
                t.get("hours", ""),
                t.get("delay_hours", ""),
                "; ".join(str(d) for d in (t.get("depends_on") or [])),
                (t.get("start") or "")[:10],
                (t.get("end") or "")[:10],
                t.get("status", ""),
                t.get("completed_on", ""),
            ]
        )
    # BOM so Excel detects UTF-8 (task names contain em-dashes)
    return "\ufeff" + buf.getvalue()
