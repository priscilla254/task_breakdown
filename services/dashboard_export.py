"""Build a self-contained, read-only Gantt dashboard for the Phase 1 project,
suitable for static hosting (e.g. GitHub Pages). Unlike tasks_to_html() in
export_service.py (a single static chart with no controls), this embeds the
scheduled task data as JSON and adds search/status-filter/full-screen in
plain JS, so no backend is needed to browse it.
"""

import json
from datetime import date

from data_manager import PROJECTS
from services.project_service import _schedule

EXPORT_FIELDS = (
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


def _task_export_dict(t):
    return {k: t.get(k) for k in EXPORT_FIELDS if t.get(k) is not None}


def build_dashboard_html(project_id: str = "phase1") -> str:
    meta = PROJECTS[project_id]
    _, _, tasks = _schedule(project_id)
    generated = date.today().isoformat()
    data = {
        "generated": generated,
        "project_name": meta["name"],
        "tasks": [_task_export_dict(t) for t in tasks],
    }
    # ensure_ascii keeps this valid inside a <script> tag; escape "</" so a
    # literal "</script" inside task text can't close the tag early.
    data_json = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    return (
        _TEMPLATE.replace("__DATA_JSON__", data_json)
        .replace("__GENERATED__", generated)
        .replace("__PROJECT_NAME__", meta["name"])
    )


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PROJECT_NAME__ — Gantt (read-only)</title>
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
  .toolbar {
    display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end;
    background: rgba(0,0,0,0.15); padding: 14px 16px; border-radius: 10px; margin: 20px 0 16px;
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
  .card-head { display: flex; align-items: center; justify-content: space-between; }
  .card-head h2 { margin: 0 0 12px; font-size: 1rem; color: #d7e2ea; }
  #expand-gantt {
    background: transparent; border: 1px solid rgba(50,195,226,0.3); color: #b8c5d0;
    padding: 6px 12px; border-radius: 6px; cursor: pointer; font: inherit; font-size: 0.78rem; margin-bottom: 12px;
  }
  #expand-gantt:hover { border-color: #32c3e2; color: #32c3e2; }
  #gantt { width: 100%; }
  #gantt-card:fullscreen { background: #3a4856; padding: 20px; display: flex; flex-direction: column; }
  #gantt-card:fullscreen #gantt { flex: 1; height: 100% !important; }
  #gantt-card::backdrop { background: #3a4856; }
  #legend { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem; color: #b8c5d0; }
  .legend-item { display: inline-flex; align-items: center; gap: 6px; }
  .legend-hint { color: #8ea0af; }
  .legend-swatch { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
  .empty { color: #8ea0af; padding: 32px; text-align: center; }
  footer { padding: 16px 32px 32px; color: #7a8d9c; font-size: 0.75rem; text-align: center; }
  a { color: #32c3e2; }
</style>
</head>
<body>
<header>
  <h1>__PROJECT_NAME__ — Timeline</h1>
  <p>Generated __GENERATED__ · view-only export, no editing here — data will not update after this snapshot.</p>
</header>
<main>
  <div class="toolbar">
    <label>Search
      <input type="search" id="search" placeholder="Task or assignee…">
    </label>
    <label>Status
      <select id="f-status">
        <option value="all">All statuses</option>
        <option value="Not started">Not started</option>
        <option value="In progress">In progress</option>
        <option value="Completed">Completed</option>
      </select>
    </label>
    <button type="button" id="clear-filters">Clear filters</button>
    <span id="summary"></span>
  </div>
  <div class="card" id="gantt-card">
    <div class="card-head">
      <h2>Timeline</h2>
      <button type="button" id="expand-gantt">⛶ Full screen</button>
    </div>
    <div id="gantt"></div>
    <div id="legend"></div>
  </div>
</main>
<footer>Static export from the Tasks Gantt app.</footer>
<script>
window.__DASHBOARD__ = __DATA_JSON__;
(function () {
  "use strict";
  var DATA = window.__DASHBOARD__;
  var STATUS_COLORS = { "Not started": "#7a8d9c", "In progress": "#32c3e2", "Completed": "#4dd4a8" };
  var ASSIGNEE_HUES = [185, 160, 200, 140, 45, 280];

  function assigneeColor(name) {
    name = (name || "").trim();
    if (!name) return null;
    var h = 0;
    for (var i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
    return "hsl(" + ASSIGNEE_HUES[Math.abs(h) % ASSIGNEE_HUES.length] + ", 55%, 58%)";
  }
  function barColor(t) {
    return assigneeColor(t.assignee) || STATUS_COLORS[t.status] || STATUS_COLORS["Not started"];
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(v) { return v ? String(v).slice(0, 10) : "—"; }
  function uniqueSorted(values) {
    var set = {};
    values.forEach(function (v) { if (v) set[v] = true; });
    return Object.keys(set).sort(function (a, b) { return a.localeCompare(b, undefined, { sensitivity: "base" }); });
  }

  var state = { search: "", status: "all" };

  function matchesSearch(t, q) {
    if (!q) return true;
    q = q.toLowerCase();
    return [t.task, t.assignee].some(function (v) {
      return v && String(v).toLowerCase().indexOf(q) !== -1;
    });
  }
  function applyFilters(tasks) {
    return tasks.filter(function (t) {
      if (!matchesSearch(t, state.search)) return false;
      if (state.status !== "all" && t.status !== state.status) return false;
      return true;
    });
  }

  function renderGantt(tasks) {
    var el = document.getElementById("gantt");
    var withDates = tasks.filter(function (t) { return t.start && t.end; });
    if (!withDates.length) {
      el.innerHTML = '<p class="empty">No tasks match the current search/filters.</p>';
      return;
    }
    var y = [], base = [], dur = [], colors = [], hover = [];
    withDates.forEach(function (t) {
      var s = new Date(t.start), e = new Date(t.end);
      y.push(t.task);
      base.push(t.start);
      dur.push(e - s);
      colors.push(barColor(t));
      var depends = (t.depends_on || []).join(", ") || "—";
      var lines = [
        "<b>" + escapeHtml(t.task) + "</b>",
        "Assignee: " + escapeHtml(t.assignee || "—"),
        "Start: " + fmtDate(t.start),
        "End: " + fmtDate(t.end),
        "Days: " + t.days,
        "Status: " + escapeHtml(t.status || ""),
        "Depends on: " + depends
      ];
      hover.push(lines.join("<br>"));
    });
    var height = Math.max(420, Math.min(y.length * 28, 9000));
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

  function renderLegend(allTasks) {
    var el = document.getElementById("legend");
    var assignees = uniqueSorted(allTasks.map(function (t) { return t.assignee; }));
    var html = assignees.map(function (name) {
      return '<span class="legend-item"><span class="legend-swatch" style="background:' + assigneeColor(name) + '"></span>' + escapeHtml(name) + "</span>";
    }).join("");
    html += '<span class="legend-item legend-hint">Bar colour = assignee when set</span>';
    html += '<span class="legend-item legend-hint">Unassigned bars, by status:</span>';
    Object.keys(STATUS_COLORS).forEach(function (label) {
      html += '<span class="legend-item"><span class="legend-swatch" style="background:' + STATUS_COLORS[label] + '"></span>' + label + "</span>";
    });
    el.innerHTML = html;
  }

  function renderSummary(filteredCount, totalCount) {
    document.getElementById("summary").textContent = "Showing " + filteredCount + " of " + totalCount + " tasks";
  }

  function sortTasks(tasks) {
    var arr = tasks.slice();
    var hasOrder = arr.some(function (t) { return t.display_order != null; });
    arr.sort(function (a, b) {
      if (hasOrder) {
        var oa = a.display_order != null ? a.display_order : Infinity;
        var ob = b.display_order != null ? b.display_order : Infinity;
        if (oa !== ob) return oa - ob;
      }
      return a.id - b.id;
    });
    return arr;
  }

  function renderAll() {
    var all = DATA.tasks;
    var filtered = sortTasks(applyFilters(all));
    renderGantt(filtered);
    renderSummary(filtered.length, all.length);
  }

  document.getElementById("search").addEventListener("input", function (e) { state.search = e.target.value; renderAll(); });
  document.getElementById("f-status").addEventListener("change", function (e) { state.status = e.target.value; renderAll(); });
  document.getElementById("clear-filters").addEventListener("click", function () {
    state.search = ""; state.status = "all";
    document.getElementById("search").value = "";
    document.getElementById("f-status").value = "all";
    renderAll();
  });

  var ganttCard = document.getElementById("gantt-card");
  var expandBtn = document.getElementById("expand-gantt");
  expandBtn.addEventListener("click", function () {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else if (ganttCard.requestFullscreen) {
      ganttCard.requestFullscreen();
    }
  });
  document.addEventListener("fullscreenchange", function () {
    var active = document.fullscreenElement === ganttCard;
    expandBtn.textContent = active ? "⛶ Exit full screen (Esc)" : "⛶ Full screen";
    setTimeout(function () {
      var el = document.getElementById("gantt");
      if (window.Plotly && el && el.data) Plotly.Plots.resize(el);
    }, 60);
  });

  renderLegend(DATA.tasks);
  renderAll();
})();
</script>
</body>
</html>
"""
