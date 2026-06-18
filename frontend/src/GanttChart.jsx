import { useMemo, useCallback } from "react";
import Plot from "react-plotly.js";
import { assigneeColor, phaseBarColor, taskBarColor, trainingRowAssigneeBorder, uniqueAssignees } from "./assigneeColors";
import { ganttTaskLabel, sortTrainingTasks } from "./trainingUtils";
import { sortProjectTasks } from "./taskSort";

const STATUS_COLORS = {
  "Not started": "#7a8d9c",
  "In progress": "#32c3e2",
  Completed: "#4dd4a8",
};

function barColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS["Not started"];
}

const TRAINING_GANTT_LIMIT = 100;
const TRAINING_GANTT_FILTERED_LIMIT = 1600;

export default function GanttChart({
  tasks,
  onTaskSelect,
  trainingMode = false,
  filtersActive = false,
}) {
  const orderedTasks = useMemo(
    () => (trainingMode ? sortTrainingTasks(tasks) : sortProjectTasks(tasks)),
    [tasks, trainingMode]
  );

  const assigneeLegend = useMemo(
    () => (trainingMode ? [] : uniqueAssignees(orderedTasks)),
    [orderedTasks, trainingMode]
  );

  const taskById = useMemo(() => {
    const map = new Map();
    for (const t of orderedTasks) map.set(t.id, t);
    return map;
  }, [orderedTasks]);

  const { data, layout, height } = useMemo(() => {
    const y = [];
    const durations = [];
    const bases = [];
    const colors = [];
    const customdata = [];

    for (const t of orderedTasks) {
      const start = new Date(t.start);
      const end = new Date(t.end);
      const label = trainingMode ? ganttTaskLabel(t) : t.task;
      y.push(label);
      durations.push(end - start);
      bases.push(start);
      colors.push(
        trainingMode
          ? phaseBarColor(t.phase)
          : taskBarColor(t, STATUS_COLORS, t.status)
      );
      customdata.push([
        t.start,
        (t.end || "").slice(0, 10),
        t.days,
        t.status,
        (t.depends_on || []).join(", ") || "—",
        t.id,
        t.assignee || "—",
        t.department || "—",
        t.subject || "—",
      ]);
    }

    const hovertemplate = trainingMode
      ? "<b>%{y}</b><br>Dept: %{customdata[7]}<br>Subject: %{customdata[8]}<br>" +
        "Assignee: %{customdata[6]}<br>Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
        "Days: %{customdata[2]}<br>Status: %{customdata[3]}<br>" +
        "Depends on: %{customdata[4]}<br><i>Click to edit</i><extra></extra>"
      : "<b>%{y}</b><br>Assignee: %{customdata[6]}<br>Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
        "Days: %{customdata[2]}<br>Status: %{customdata[3]}<br>" +
        "Depends on: %{customdata[4]}<br><i>Click to edit</i><extra></extra>";

    return {
      data: [
        {
          type: "bar",
          orientation: "h",
          y,
          x: durations,
          base: bases,
          marker: {
            color: colors,
            line: { color: "rgba(255,255,255,0.2)", width: 0.5 },
          },
          customdata,
          hovertemplate,
        },
      ],
      layout: {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "DM Sans, sans-serif", color: "#b8c5d0", size: 11 },
        title: { text: "" },
        xaxis: {
          type: "date",
          gridcolor: "rgba(50,195,226,0.12)",
          linecolor: "rgba(50,195,226,0.25)",
          tickfont: { color: "#b8c5d0" },
        },
        yaxis: {
          autorange: "reversed",
          showticklabels: false,
          automargin: false,
          gridcolor: "rgba(50,195,226,0.08)",
        },
        margin: { l: 12, r: 24, t: 16, b: 40 },
        bargap: 0.18,
        showlegend: false,
        hoverlabel: {
          bgcolor: "#465667",
          bordercolor: "#32c3e2",
          font: { color: "#f4f8fb" },
        },
      },
      height: Math.max(
        520,
        Math.min(orderedTasks.length * (trainingMode ? 34 : 30), trainingMode ? 2400 : 8000)
      ),
    };
  }, [orderedTasks, trainingMode]);

  const selectTask = useCallback(
    (task) => {
      if (task && onTaskSelect) onTaskSelect(task);
    },
    [onTaskSelect]
  );

  const handleClick = useCallback(
    (event) => {
      const point = event?.points?.[0];
      if (!point) return;
      if (point.customdata) {
        selectTask(taskById.get(point.customdata[5]));
        return;
      }
      const byName = orderedTasks.find(
        (t) => (trainingMode ? ganttTaskLabel(t) : t.task) === point.y
      );
      if (byName) selectTask(byName);
    },
    [taskById, orderedTasks, trainingMode, selectTask]
  );

  if (!orderedTasks.length) {
    return <p className="loading">No tasks to display</p>;
  }

  const taskLimit = trainingMode
    ? filtersActive
      ? TRAINING_GANTT_FILTERED_LIMIT
      : TRAINING_GANTT_LIMIT
    : Infinity;

  if (trainingMode && orderedTasks.length > taskLimit) {
    return (
      <p className="empty-state">
        Gantt chart shows up to <strong>{taskLimit}</strong> tasks at once (
        {orderedTasks.length} match your filters).{" "}
        {filtersActive
          ? "Try a subject or phase filter to narrow further, or use"
          : "Use department, subject, or phase filters to narrow the list, or switch to"}{" "}
        <strong>Task list</strong> for the full breakdown.
      </p>
    );
  }

  return (
    <div className="gantt-wrap">
      <p className="gantt-hint">
        Custom row order in the list; bar position reflects scheduled dates. Click{" "}
        {trainingMode ? "a row or bar" : "a task name or bar"} to open documentation.
        {trainingMode
          ? " Bar colour = phase. Row border = assignee."
          : " Bar colour = assignee when set."}
      </p>
      <div className="gantt-chart-row" style={{ height }}>
        <div
          className={`gantt-labels-col ${trainingMode ? "gantt-labels-col-training" : ""}`}
          aria-label="Tasks"
        >
          {orderedTasks.map((t) => {
            const borderColor = trainingMode
              ? trainingRowAssigneeBorder(t.assignee)
              : assigneeColor(t.assignee) || barColor(t.status);
            return (
              <button
                key={t.id}
                type="button"
                className={`gantt-task-label ${trainingMode ? "gantt-task-label-training" : "gantt-task-label-phase1"}`}
                style={{ borderLeftColor: borderColor }}
                onClick={() => selectTask(t)}
                title={trainingMode ? ganttTaskLabel(t) : t.task}
              >
                {trainingMode ? (
                  <span className="gantt-label-text">{ganttTaskLabel(t)}</span>
                ) : (
                  <>
                    <span
                      className="gantt-status-dot"
                      style={{ background: barColor(t.status) }}
                      title={t.status}
                      aria-label={t.status}
                    />
                    <span className="gantt-label-text">{t.task}</span>
                  </>
                )}
              </button>
            );
          })}
        </div>
        <div className="gantt-plot-col">
          <Plot
            data={data}
            layout={{ ...layout, height }}
            config={{ responsive: true, displayModeBar: true, displaylogo: false }}
            style={{ width: "100%", cursor: "pointer" }}
            useResizeHandler
            onClick={handleClick}
          />
        </div>
      </div>
      <div className="legend">
        {trainingMode ? (
          <>
            <span className="legend-item legend-hint">Bar colour = phase</span>
            <span className="legend-item">
              <span className="legend-swatch legend-swatch-phase-content" />
              Content
            </span>
            <span className="legend-item">
              <span className="legend-swatch legend-swatch-phase-development" />
              Development
            </span>
            <span className="legend-item">
              <span className="legend-swatch legend-swatch-phase-upload" />
              Upload
            </span>
            <span className="legend-item legend-hint">Row border = assignee</span>
            <span className="legend-item">
              <span className="legend-swatch legend-swatch-priscilla" />
              Priscilla
            </span>
            <span className="legend-item">
              <span className="legend-swatch legend-swatch-unassigned" />
              Unassigned
            </span>
          </>
        ) : (
          <>
            {assigneeLegend.map((name) => (
              <span key={name} className="legend-item">
                <span
                  className="legend-swatch"
                  style={{ background: assigneeColor(name) }}
                />
                {name}
              </span>
            ))}
            <span className="legend-item legend-hint">
              Dot beside task name = status. Bar colour = assignee when set.
            </span>
            <span className="legend-item legend-hint">Unassigned bars:</span>
            {Object.entries(STATUS_COLORS).map(([label, color]) => (
              <span key={`unassigned-${label}`} className="legend-item legend-item-compact">
                <span className="legend-swatch legend-swatch-sm" style={{ background: color }} />
                {label}
              </span>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
