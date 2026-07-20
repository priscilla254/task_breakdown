"""Build a self-contained, read-only dashboard (Gantt + searchable/filterable
task table, tab-switchable per project) suitable for static hosting, e.g.
GitHub Pages. Unlike tasks_to_html() in export_service.py (one static chart),
this embeds the scheduled task data as JSON and re-implements the live app's
tabs/search/filters in plain JS, so no backend is needed to browse it.
"""

import json
from datetime import date

from data_manager import PROJECTS
from services.project_service import _schedule

EXPORT_FIELDS_COMMON = (
    "id",
    "task",
    "days",
    "status",
    "assignee",
    "depends_on",
    "start",
    "end",
    "completed_on",
    "delay_days",
    "display_order",
)
EXPORT_FIELDS_TRAINING = ("department", "subject", "phase", "module_index", "step_id")


def _task_export_dict(t):
    out = {k: t.get(k) for k in EXPORT_FIELDS_COMMON if t.get(k) is not None}
    for k in EXPORT_FIELDS_TRAINING:
        if t.get(k) is not None:
            out[k] = t[k]
    return out


def _project_payload(project_id):
    meta = PROJECTS[project_id]
    _, _, tasks = _schedule(project_id)
    return {
        "id": project_id,
        "name": meta["name"],
        "tasks": [_task_export_dict(t) for t in tasks],
    }


def build_dashboard_html(project_ids=None) -> str:
    project_ids = list(project_ids) if project_ids else list(PROJECTS)
    generated = date.today().isoformat()
    data = {
        "generated": generated,
        "default": project_ids[0],
        "projects": {pid: _project_payload(pid) for pid in project_ids},
    }
    # ensure_ascii keeps this valid inside a <script> tag; escape "</" so a
    # literal "</script" inside task text can't close the tag early.
    data_json = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    return _TEMPLATE.replace("__DATA_JSON__", data_json).replace("__GENERATED__", generated)


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tasks Gantt — read-only snapshot</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "DM Sans", system-ui, -apple-system, sans-serif;
    background: linear-gradient(145deg, #3a4856 0%, #465667 45%, #3d4f5e 100%);
    color: #f4f8fb;
    min-height: 100vh;
  }
  header { padding: 24px 32px 4px; }
  header h1 { margin: 0 0 4px; font-size: 1.4rem; }
  header p { margin: 0; color: #b8c5d0; font-size: 0.85rem; }
  main { padding: 0 32px 48px; max-width: 1400px; margin: 0 auto; }
  .tabs { display: flex; gap: 8px; margin: 20px 0 16px; }
  .tab-btn {
    background: transparent; border: 1px solid rgba(50,195,226,0.3); color: #b8c5d0;
    padding: 8px 18px; border-radius: 8px; cursor: pointer; font: inherit; font-weight: 600;
  }
  .tab-btn.active { background: #32c3e2; color: #28384a; border-color: #32c3e2; }
  .toolbar {
    display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end;
    background: rgba(0,0,0,0.15); padding: 14px 16px; border-radius: 10px; margin-bottom: 16px;
  }
  .toolbar label { display: flex; flex-direction: column; gap: 4px; font-size: 0.72rem; color: #8ea0af; text-transform: uppercase; letter-spacing: 0.03em; }
  .toolbar input[type=search], .toolbar select {
    background: #3a4856; border: 1px solid rgba(50,195,226,0.25); color: #f4f8fb;
    padding: 8px 10px; border-radius: 6px; font: inherit; font-size: 0.85rem;
  }
  .toolbar input[type=search] { min-width: 220px; }
  #clear-filters { align-self: flex-end; background: transparent; border: 1px solid rgba(255,255,255,0.15); color: #b8c5d0; padding: 8px 12px; border-radius: 6px; cursor: pointer; font: inherit; font-size: 0.8rem; }
  #summary { margin-left: auto; align-self: center; font-size: 0.82rem; color: #b8c5d0; white-space: nowrap; }
  .card { background: rgba(0,0,0,0.15); border-radius: 12px; padding: 16px; margin-bottom: 24px; }
  .card h2 { margin: 0 0 12px; font-size: 1rem; color: #d7e2ea; }
  #gantt { width: 100%; }
  .table-scroll { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.06); white-space: nowrap; }
  th { color: #8ea0af; font-weight: 600; text-transform: uppercase; font-size: 0.68rem; letter-spacing: 0.04em; position: sticky; top: 0; background: #3a4856; }
  tbody tr:hover { background: rgba(50,195,226,0.06); }
  td.wrap { white-space: normal; min-width: 220px; }
  .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .empty { color: #8ea0af; padding: 32px; text-align: center; }
  footer { padding: 16px 32px 32px; color: #7a8d9c; font-size: 0.75rem; text-align: center; }
  a { color: #32c3e2; }
</style>
</head>
<body>
<header>
  <h1>Tasks Gantt — read-only snapshot</h1>
  <p>Generated __GENERATED__ · view-only export, no editing here — data will not update after this snapshot.</p>
</header>
<main>
  <div class="tabs" id="tabs"></div>
  <div class="toolbar">
    <label>Search
      <input type="search" id="search" placeholder="Task, assignee, department…">
    </label>
    <div id="filters" style="display:contents"></div>
    <button type="button" id="clear-filters">Clear filters</button>
    <span id="summary"></span>
  </div>
  <div class="card">
    <h2>Timeline</h2>
    <div id="gantt"></div>
  </div>
  <div class="card">
    <h2>Task list</h2>
    <div class="table-scroll">
      <table id="table"><thead></thead><tbody></tbody></table>
    </div>
  </div>
</main>
<footer>Static export from the Tasks Gantt app.</footer>
<script>
window.__DASHBOARD__ = __DATA_JSON__;
(function () {
  "use strict";
  var DATA = window.__DASHBOARD__;
  var STATUS_COLORS = { "Not started": "#7a8d9c", "In progress": "#32c3e2", "Completed": "#4dd4a8" };
  var PHASE_COLORS = { content: "#4dd4a8", development: "#32c3e2", upload: "#c495ff" };
  var PHASE_ORDER = { content: 0, development: 1, upload: 2 };
  var ASSIGNEE_HUES = [185, 160, 200, 140, 45, 280];

  function assigneeColor(name) {
    name = (name || "").trim();
    if (!name) return null;
    var h = 0;
    for (var i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
    return "hsl(" + ASSIGNEE_HUES[Math.abs(h) % ASSIGNEE_HUES.length] + ", 55%, 58%)";
  }
  function phaseColor(phase) { return PHASE_COLORS[phase] || "#7a8d9c"; }
  function barColor(t, training) {
    if (training) return phaseColor(t.phase);
    return assigneeColor(t.assignee) || STATUS_COLORS[t.status] || STATUS_COLORS["Not started"];
  }
  function stepKey(id) {
    if (!id) return [99, 99];
    var p = String(id).split(".");
    var a = parseInt(p[0], 10), b = parseInt(p[1], 10);
    return [isNaN(a) ? 99 : a, isNaN(b) ? 99 : b];
  }
  function ganttLabel(t) {
    var parts = [];
    if (t.department) parts.push(t.department);
    if (t.subject) parts.push(t.subject);
    parts.push(t.task);
    return parts.join(" › ");
  }
  function trainingCmp(a, b) {
    var dept = (a.department || "").localeCompare(b.department || "", undefined, { sensitivity: "base" });
    if (dept) return dept;
    var sub = (a.subject || "").localeCompare(b.subject || "", undefined, { sensitivity: "base" });
    if (sub) return sub;
    var ma = a.module_index != null ? a.module_index : a.id;
    var mb = b.module_index != null ? b.module_index : b.id;
    if (ma !== mb) return ma - mb;
    var pa = PHASE_ORDER[a.phase] != null ? PHASE_ORDER[a.phase] : 99;
    var pb = PHASE_ORDER[b.phase] != null ? PHASE_ORDER[b.phase] : 99;
    if (pa !== pb) return pa - pb;
    var ka = stepKey(a.step_id), kb = stepKey(b.step_id);
    if (ka[0] !== kb[0]) return ka[0] - kb[0];
    if (ka[1] !== kb[1]) return ka[1] - kb[1];
    return a.id - b.id;
  }
  function sortTasks(tasks, training) {
    var arr = tasks.slice();
    var hasOrder = arr.some(function (t) { return t.display_order != null; });
    var cmp = training ? trainingCmp : function (a, b) { return a.id - b.id; };
    if (hasOrder) {
      arr.sort(function (a, b) {
        var oa = a.display_order != null ? a.display_order : Infinity;
        var ob = b.display_order != null ? b.display_order : Infinity;
        if (oa !== ob) return oa - ob;
        return cmp(a, b);
      });
    } else {
      arr.sort(cmp);
    }
    return arr;
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(v) { return v ? String(v).slice(0, 10) : "—"; }

  var state = { project: DATA.default, search: "", status: "all", phase: "all", department: "all", subject: "all", assignee: "all" };

  function isTraining() { return state.project === "training"; }
  function currentTasks() { return DATA.projects[state.project].tasks; }

  function matchesSearch(t, q) {
    if (!q) return true;
    q = q.toLowerCase();
    return [t.task, t.assignee, t.department, t.subject].some(function (v) {
      return v && String(v).toLowerCase().indexOf(q) !== -1;
    });
  }
  function applyFilters(tasks) {
    var training = isTraining();
    return tasks.filter(function (t) {
      if (!matchesSearch(t, state.search)) return false;
      if (!training) {
        if (state.status !== "all" && t.status !== state.status) return false;
      } else {
        if (state.phase !== "all" && t.phase !== state.phase) return false;
        if (state.department !== "all" && (t.department || "") !== state.department) return false;
        if (state.subject !== "all" && (t.subject || "") !== state.subject) return false;
        if (state.assignee === "unassigned") {
          if (t.assignee && String(t.assignee).trim()) return false;
        } else if (state.assignee !== "all" && (t.assignee || "") !== state.assignee) {
          return false;
        }
      }
      return true;
    });
  }

  function renderTabs() {
    var el = document.getElementById("tabs");
    el.innerHTML = "";
    Object.keys(DATA.projects).forEach(function (pid) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tab-btn" + (pid === state.project ? " active" : "");
      btn.textContent = DATA.projects[pid].name;
      btn.addEventListener("click", function () {
        if (state.project === pid) return;
        state.project = pid;
        state.status = "all"; state.phase = "all"; state.department = "all";
        state.subject = "all"; state.assignee = "all";
        renderTabs();
        renderFilterControls();
        renderAll();
      });
      el.appendChild(btn);
    });
  }

  function uniqueSorted(values) {
    var set = {};
    values.forEach(function (v) { if (v) set[v] = true; });
    return Object.keys(set).sort(function (a, b) { return a.localeCompare(b, undefined, { sensitivity: "base" }); });
  }

  function renderFilterControls() {
    var training = isTraining();
    var el = document.getElementById("filters");
    var tasks = currentTasks();
    if (!training) {
      el.innerHTML =
        '<label>Status<select id="f-status">' +
        ["all", "Not started", "In progress", "Completed"].map(function (v) {
          return '<option value="' + v + '">' + (v === "all" ? "All statuses" : v) + "</option>";
        }).join("") +
        "</select></label>";
      document.getElementById("f-status").addEventListener("change", function (e) { state.status = e.target.value; renderAll(); });
      return;
    }
    var departments = uniqueSorted(tasks.map(function (t) { return t.department; }));
    var subjects = uniqueSorted(tasks.map(function (t) { return t.subject; }));
    var assignees = uniqueSorted(tasks.map(function (t) { return t.assignee; }));
    function opts(values) { return values.map(function (v) { return '<option value="' + escapeHtml(v) + '">' + escapeHtml(v) + "</option>"; }).join(""); }
    el.innerHTML =
      '<label>Phase<select id="f-phase"><option value="all">All</option><option value="content">Content</option><option value="development">Development</option><option value="upload">Upload</option></select></label>' +
      '<label>Department<select id="f-department"><option value="all">All</option>' + opts(departments) + "</select></label>" +
      '<label>Subject<select id="f-subject"><option value="all">All</option>' + opts(subjects) + "</select></label>" +
      '<label>Assignee<select id="f-assignee"><option value="all">All</option><option value="unassigned">Unassigned</option>' + opts(assignees) + "</select></label>";
    document.getElementById("f-phase").addEventListener("change", function (e) { state.phase = e.target.value; renderAll(); });
    document.getElementById("f-department").addEventListener("change", function (e) { state.department = e.target.value; renderAll(); });
    document.getElementById("f-subject").addEventListener("change", function (e) { state.subject = e.target.value; renderAll(); });
    document.getElementById("f-assignee").addEventListener("change", function (e) { state.assignee = e.target.value; renderAll(); });
  }

  function statusCell(s) {
    var color = STATUS_COLORS[s] || STATUS_COLORS["Not started"];
    return '<span class="status-dot" style="background:' + color + '"></span>' + escapeHtml(s || "");
  }

  function renderTable(tasks, training) {
    var thead = document.querySelector("#table thead");
    var tbody = document.querySelector("#table tbody");
    var cols = training
      ? ["ID", "Department", "Subject", "Task", "Assignee", "Phase", "Days", "Start", "End", "Status", "Depends on"]
      : ["ID", "Task", "Assignee", "Days", "Start", "End", "Status", "Depends on"];
    thead.innerHTML = "<tr>" + cols.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr>";
    if (!tasks.length) {
      tbody.innerHTML = '<tr><td colspan="' + cols.length + '" class="empty">No tasks match the current search/filters.</td></tr>';
      return;
    }
    tbody.innerHTML = tasks.map(function (t) {
      var depends = (t.depends_on || []).join(", ") || "—";
      var cells = training
        ? [t.id, escapeHtml(t.department || "—"), escapeHtml(t.subject || "—"), '<span class="wrap">' + escapeHtml(t.task) + "</span>", escapeHtml(t.assignee || "—"), escapeHtml(t.phase || "—"), t.days, fmtDate(t.start), fmtDate(t.end), statusCell(t.status), depends]
        : [t.id, '<span class="wrap">' + escapeHtml(t.task) + "</span>", escapeHtml(t.assignee || "—"), t.days, fmtDate(t.start), fmtDate(t.end), statusCell(t.status), depends];
      return "<tr>" + cells.map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>";
    }).join("");
  }

  function renderGantt(tasks, training) {
    var el = document.getElementById("gantt");
    var withDates = tasks.filter(function (t) { return t.start && t.end; });
    if (!withDates.length) {
      el.innerHTML = '<p class="empty">No tasks match the current search/filters.</p>';
      return;
    }
    var y = [], base = [], dur = [], colors = [], hover = [];
    withDates.forEach(function (t) {
      var s = new Date(t.start), e = new Date(t.end);
      var label = training ? ganttLabel(t) : t.task;
      y.push(label);
      base.push(t.start);
      dur.push(e - s);
      colors.push(barColor(t, training));
      var depends = (t.depends_on || []).join(", ") || "—";
      var lines = ["<b>" + escapeHtml(label) + "</b>"];
      if (training) {
        lines.push("Dept: " + escapeHtml(t.department || "—"));
        lines.push("Subject: " + escapeHtml(t.subject || "—"));
      }
      lines.push("Assignee: " + escapeHtml(t.assignee || "—"));
      lines.push("Start: " + fmtDate(t.start));
      lines.push("End: " + fmtDate(t.end));
      lines.push("Days: " + t.days);
      lines.push("Status: " + escapeHtml(t.status || ""));
      lines.push("Depends on: " + depends);
      hover.push(lines.join("<br>"));
    });
    var height = Math.max(420, Math.min(y.length * (training ? 26 : 28), 9000));
    el.style.height = height + "px";
    Plotly.react(el, [{
      type: "bar", orientation: "h", y: y, x: dur, base: base,
      marker: { color: colors, line: { color: "rgba(255,255,255,0.2)", width: 0.5 } },
      hovertext: hover, hoverinfo: "text"
    }], {
      paper_bgcolor: "transparent", plot_bgcolor: "transparent",
      font: { family: "DM Sans, sans-serif", color: "#b8c5d0", size: 11 },
      xaxis: { type: "date", gridcolor: "rgba(50,195,226,0.12)", linecolor: "rgba(50,195,226,0.25)" },
      yaxis: { autorange: "reversed", gridcolor: "rgba(50,195,226,0.08)", automargin: true },
      margin: { l: 10, r: 24, t: 10, b: 40 },
      bargap: 0.18, showlegend: false,
      hoverlabel: { bgcolor: "#465667", bordercolor: "#32c3e2", font: { color: "#f4f8fb" } }
    }, { responsive: true, displaylogo: false });
  }

  function renderSummary(filteredCount, totalCount) {
    document.getElementById("summary").textContent = "Showing " + filteredCount + " of " + totalCount + " tasks";
  }

  function renderAll() {
    var training = isTraining();
    var all = currentTasks();
    var filtered = sortTasks(applyFilters(all), training);
    renderTable(filtered, training);
    renderGantt(filtered, training);
    renderSummary(filtered.length, all.length);
  }

  document.getElementById("search").addEventListener("input", function (e) { state.search = e.target.value; renderAll(); });
  document.getElementById("clear-filters").addEventListener("click", function () {
    state.search = ""; state.status = "all"; state.phase = "all"; state.department = "all"; state.subject = "all"; state.assignee = "all";
    document.getElementById("search").value = "";
    renderFilterControls();
    renderAll();
  });

  renderTabs();
  renderFilterControls();
  renderAll();
})();
</script>
</body>
</html>
"""
