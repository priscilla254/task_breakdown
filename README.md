# Data science and Innovation — Phase 1

A local web application for planning and tracking the **Phase 1** rollout: Excel template → Azure SQL database → ETL → FastAPI backend → Power BI dashboards. It provides an interactive Gantt chart, task management, and per-task documentation.

## What it does

The app loads your project plan from a JSON file and **calculates a schedule automatically** based on:

- **Dependencies** — each task lists which other tasks must finish first (`depends_on`). Tasks with no dependencies can run in parallel.
- **Duration** — each task has a number of **project hours** (not calendar days).
- **Working calendar** — hours are spread across Mon–Thu only, using half of your nominal daily capacity (configured in `utils.py`).
- **Project start date** — the anchor for tasks with no predecessors.

When you change hours, dependencies, status, or a manual start date on a task, the **entire timeline recalculates** and downstream tasks shift accordingly.

## Main features

| Feature | Description |
|--------|-------------|
| **Gantt chart** | Horizontal timeline with colour by status (not started / in progress / completed). Click a bar or task name to open documentation. |
| **Task list** | Table view with inline edits; click a row to document, or use **Schedule** for dates and hours. |
| **Task documentation** | Full-page log per task: add timestamped notes without changing the schedule. |
| **Edit schedule** | Modal to update status, duration, optional fixed start date, and dependencies. |
| **Add task** | Create new tasks with name, hours, dependencies, and status; ID is assigned automatically. |
| **Project start** | Change the global kickoff date from the header. |

## Architecture

```
tasks_gantt/
├── main.py              # FastAPI REST API
├── data_manager.py      # Read/write tasks.json and audit log.txt
├── utils.py             # Dependency scheduling + working-hours calendar
├── data/
│   ├── tasks.json       # Project plan (source of truth)
│   └── log.txt          # Backend audit trail (not shown in UI)
├── frontend/            # React + Vite UI (brand colours: #465667, #32c3e2)
└── static/dist/         # Production build served by FastAPI
```

**Backend:** Python, FastAPI, JSON file storage (no database server required).

**Frontend:** React, Plotly (Gantt), Vite. API calls go to `/api/*`.

## Running the application

### Prerequisites

- Python 3.10+
- Node.js 18+ (for building or developing the UI)

```bash
pip install fastapi uvicorn
```

### Production (single server)

```bash
cd frontend
npm install
npm run build

cd ..
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/**

### Frontend development (hot reload)

Terminal 1:

```bash
uvicorn main:app --reload
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (API is proxied to port 8000).

## Data format (`data/tasks.json`)

```json
{
  "project_start": "2026-06-01",
  "gap_days": 1,
  "tasks": [
    {
      "id": 1,
      "task": "1. Finalise Excel template",
      "hours": 14,
      "depends_on": [],
      "status": "Not started",
      "log": ""
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `project_start` | Date when tasks with no dependencies can begin |
| `gap_days` | Calendar days between chained tasks (default 1) |
| `id` | Unique task identifier |
| `task` | Display name |
| `hours` | Project hours to complete the task |
| `depends_on` | List of task IDs that must finish first |
| `status` | `Not started`, `In progress`, or `Completed` |
| `log` | Per-task documentation (timestamped entries appended via UI) |
| `fixed_start` | Optional manual start date (set via UI; cannot be earlier than dependencies allow) |

Computed fields `start` and `end` are returned by the API but not stored in JSON.

## API overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/tasks` | List tasks with computed start/end dates |
| POST | `/api/tasks` | Create a new task |
| PUT | `/api/tasks/{id}` | Update task fields |
| POST | `/api/tasks/{id}/log` | Append a log entry to a task |
| PUT | `/api/project-start` | Change project start date |

## Working hours (scheduling)

Default calendar in `utils.py`:

| Day | Project hours |
|-----|----------------|
| Monday | 2.5 |
| Tuesday–Thursday | 3.75 each |
| Friday–Sunday | 0 |

Adjust `RAW_DAILY_HOURS` if your availability changes (project hours are half of raw hours).

## Notes

- This tool plans the **Phase 1 project**; it is not the production Excel/ETL/Power BI system itself.
- Invalid dependency graphs (cycles or unknown IDs) return an error and do not save.
- Backend changes are also appended to `data/log.txt` for audit purposes.
