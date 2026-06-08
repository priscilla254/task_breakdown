import { useMemo, useCallback } from "react";
import Plot from "react-plotly.js";
import { ganttTaskLabel, sortTrainingTasks } from "./trainingUtils";

const STATUS_COLORS = {
  "Not started": "#7a8d9c",
  "In progress": "#32c3e2",
  Completed: "#4dd4a8",
};

function barColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS["Not started"];
}

function assigneeAccent(name) {
  if (!name) return null;
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  const hues = [185, 160, 200, 140, 45, 280];
  return `hsl(${hues[Math.abs(h) % hues.length]}, 55%, 58%)`;
}

export default function GanttChart({ tasks, onTaskSelect, trainingMode = false }) {
  const orderedTasks = useMemo(
    () => (trainingMode ? sortTrainingTasks(tasks) : tasks),
    [tasks, trainingMode]
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
      colors.push(barColor(t.status));
      customdata.push([
        t.start,
        (t.end || "").slice(0, 10),
        t.hours,
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
        "Hours: %{customdata[2]}<br>Status: %{customdata[3]}<br>" +
        "Depends on: %{customdata[4]}<br><i>Click to edit</i><extra></extra>"
      : "<b>%{y}</b><br>Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
        "Hours: %{customdata[2]}<br>Status: %{customdata[3]}<br>" +
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
      height: Math.max(520, orderedTasks.length * (trainingMode ? 34 : 30)),
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

  return (
    <div className="gantt-wrap">
      <p className="gantt-hint">
        {trainingMode
          ? "Grouped by department → subject. Click a row or bar to open documentation."
          : "Click a task name or bar to open documentation"}
      </p>
      <div className="gantt-chart-row" style={{ height }}>
        <div
          className={`gantt-labels-col ${trainingMode ? "gantt-labels-col-training" : ""}`}
          aria-label="Tasks"
        >
          {orderedTasks.map((t) => {
            const accent = trainingMode ? assigneeAccent(t.assignee) : null;
            return (
              <button
                key={t.id}
                type="button"
                className={`gantt-task-label ${trainingMode ? "gantt-task-label-training" : ""}`}
                style={{
                  borderLeftColor: accent || barColor(t.status),
                }}
                onClick={() => selectTask(t)}
                title={trainingMode ? ganttTaskLabel(t) : "Click to edit"}
              >
                {trainingMode ? (
                  <>
                    <span className="gantt-label-text">{ganttTaskLabel(t)}</span>
                    {t.assignee ? (
                      <span className="assignee-pill">{t.assignee}</span>
                    ) : null}
                  </>
                ) : (
                  t.task
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
        {Object.entries(STATUS_COLORS).map(([label, color]) => (
          <span key={label} className="legend-item">
            <span className="legend-swatch" style={{ background: color }} />
            {label}
          </span>
        ))}
        {trainingMode ? (
          <span className="legend-item legend-hint">
            Left border colour = assignee (when set)
          </span>
        ) : null}
      </div>
    </div>
  );
}
