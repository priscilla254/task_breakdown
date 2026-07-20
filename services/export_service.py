"""Build CSV and interactive HTML exports of a project's scheduled task list."""

import csv
import io
from datetime import date, datetime

import plotly.graph_objects as go

from services.project_service import _schedule

STATUS_COLORS = {
    "Not started": "#7a8d9c",
    "In progress": "#32c3e2",
    "Completed": "#4dd4a8",
}

PHASE_BAR_COLORS = {
    "content": "#4dd4a8",
    "development": "#32c3e2",
    "upload": "#c495ff",
}
PHASE_BAR_COLOR_OTHER = "#7a8d9c"

# Same hue set/order as frontend/src/assigneeColors.js so exported charts
# colour assignees identically to the live app.
ASSIGNEE_HUES = [185, 160, 200, 140, 45, 280]

PHASE_ORDER = {"content": 0, "development": 1, "upload": 2}

COLUMNS = [
    "ID",
    "Task",
    "Phase",
    "Department",
    "Subject",
    "Assignee",
    "Days",
    "Delay days",
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
                t.get("days", ""),
                t.get("delay_days", ""),
                "; ".join(str(d) for d in (t.get("depends_on") or [])),
                (t.get("start") or "")[:10],
                (t.get("end") or "")[:10],
                t.get("status", ""),
                t.get("completed_on", ""),
            ]
        )
    # BOM so Excel detects UTF-8 (task names contain em-dashes)
    return "\ufeff" + buf.getvalue()


def _to_int32(n: int) -> int:
    n &= 0xFFFFFFFF
    return n - 0x100000000 if n & 0x80000000 else n


def _assignee_color(name):
    """Port of assigneeColor() in frontend/src/assigneeColors.js (same hash)."""
    name = (name or "").strip()
    if not name:
        return None
    h = 0
    for ch in name:
        shifted = _to_int32((_to_int32(h) << 5) & 0xFFFFFFFF)
        h = ord(ch) + (shifted - h)
    hue = ASSIGNEE_HUES[abs(int(h)) % len(ASSIGNEE_HUES)]
    return f"hsl({hue}, 55%, 58%)"


def _phase_color(phase):
    return PHASE_BAR_COLORS.get((phase or "").lower(), PHASE_BAR_COLOR_OTHER)


def _bar_color(task, training):
    if training:
        return _phase_color(task.get("phase"))
    assignee_color = _assignee_color(task.get("assignee"))
    if assignee_color:
        return assignee_color
    return STATUS_COLORS.get(task.get("status"), STATUS_COLORS["Not started"])


def _step_sort_key(step_id):
    if not step_id:
        return (99, 99)
    parts = str(step_id).split(".")

    def _as_int(p):
        try:
            return int(p)
        except (TypeError, ValueError):
            return 99

    first = _as_int(parts[0]) if parts else 99
    second = _as_int(parts[1]) if len(parts) > 1 else 99
    return (first, second)


def _training_sort_key(t):
    return (
        (t.get("department") or "").lower(),
        (t.get("subject") or "").lower(),
        t.get("module_index", t.get("id")),
        PHASE_ORDER.get((t.get("phase") or "").lower(), 99),
        _step_sort_key(t.get("step_id")),
        t.get("id"),
    )


def _order_tasks(tasks, training):
    key_fn = _training_sort_key if training else (lambda t: (t.get("id"),))
    if any(t.get("display_order") is not None for t in tasks):
        inf = float("inf")
        return sorted(
            tasks,
            key=lambda t: (
                t["display_order"] if t.get("display_order") is not None else inf,
                key_fn(t),
            ),
        )
    return sorted(tasks, key=key_fn)


def _task_label(t, training):
    if not training:
        return t.get("task", "")
    parts = [p for p in (t.get("department"), t.get("subject")) if p]
    parts.append(t.get("task", ""))
    return " \u203a ".join(parts)


def build_gantt_figure(project_id: str) -> go.Figure:
    """Build a Plotly Gantt figure matching the live app's GanttChart.jsx look."""
    _, _, tasks = _schedule(project_id)
    training = project_id == "training"
    ordered = _order_tasks(tasks, training)

    labels, bases, durations, colors, hover_text = [], [], [], [], []

    for t in ordered:
        start, end = t.get("start"), t.get("end")
        if not start or not end:
            continue
        start_dt = datetime.fromisoformat(start[:19])
        end_dt = datetime.fromisoformat(end[:19])
        label = _task_label(t, training)

        labels.append(label)
        bases.append(start_dt)
        durations.append((end_dt - start_dt).total_seconds() * 1000)  # ms, for Plotly's date axis
        colors.append(_bar_color(t, training))

        depends = ", ".join(str(d) for d in (t.get("depends_on") or [])) or "\u2014"
        lines = [f"<b>{label}</b>"]
        if training:
            lines.append(f"Dept: {t.get('department') or '\u2014'}")
            lines.append(f"Subject: {t.get('subject') or '\u2014'}")
        lines += [
            f"Assignee: {t.get('assignee') or '\u2014'}",
            f"Start: {start[:10]}",
            f"End: {end[:10]}",
            f"Days: {t.get('days')}",
            f"Status: {t.get('status')}",
            f"Depends on: {depends}",
        ]
        hover_text.append("<br>".join(lines))

    fig = go.Figure(
        go.Bar(
            x=durations,
            y=labels,
            base=bases,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.2)", width=0.5)),
            hovertext=hover_text,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title=f"{project_id.title()} \u2014 Gantt export ({date.today().isoformat()})",
        paper_bgcolor="#1b2530",
        plot_bgcolor="#1b2530",
        font=dict(family="DM Sans, Arial, sans-serif", color="#b8c5d0", size=12),
        xaxis=dict(
            type="date",
            gridcolor="rgba(50,195,226,0.12)",
            linecolor="rgba(50,195,226,0.25)",
        ),
        yaxis=dict(
            autorange="reversed",
            gridcolor="rgba(50,195,226,0.08)",
            automargin=True,
        ),
        margin=dict(l=10, r=24, t=60, b=40),
        bargap=0.18,
        height=max(520, min(len(ordered) * (34 if training else 26), 8000)),
        hoverlabel=dict(bgcolor="#465667", bordercolor="#32c3e2", font=dict(color="#f4f8fb")),
    )
    return fig


def tasks_to_html(project_id: str, embed_js: bool = True) -> str:
    """Render the project's Gantt chart as a self-contained interactive HTML page.

    embed_js=True inlines plotly.js (~4.5MB) so the file opens with no internet
    connection (e.g. archiving/emailing it). embed_js=False loads plotly.js from
    a CDN for a much smaller download when served by the running app.
    """
    fig = build_gantt_figure(project_id)
    return fig.to_html(
        full_html=True,
        include_plotlyjs=True if embed_js else "cdn",
        config={"responsive": True, "displaylogo": False},
    )
