import { useMemo, useCallback } from "react";
import Plot from "react-plotly.js";

const STATUS_COLORS = {
  "Not started": "#7a8d9c",
  "In progress": "#32c3e2",
  Completed: "#4dd4a8",
};

function barColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS["Not started"];
}

export default function GanttChart({ tasks, onTaskSelect }) {
  const taskById = useMemo(() => {
    const map = new Map();
    for (const t of tasks) map.set(t.id, t);
    return map;
  }, [tasks]);

  const { data, layout, height } = useMemo(() => {
    const y = [];
    const durations = [];
    const bases = [];
    const colors = [];
    const customdata = [];

    for (const t of tasks) {
      const start = new Date(t.start);
      const end = new Date(t.end);
      y.push(t.task);
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
      ]);
    }

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
          hovertemplate:
            "<b>%{y}</b><br>Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
            "Hours: %{customdata[2]}<br>Status: %{customdata[3]}<br>" +
            "Depends on: %{customdata[4]}<br>" +
            "<i>Click to edit</i><extra></extra>",
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
      height: Math.max(520, tasks.length * 30),
    };
  }, [tasks]);

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
      const byName = tasks.find((t) => t.task === point.y);
      if (byName) selectTask(byName);
    },
    [taskById, tasks, selectTask]
  );

  if (!tasks.length) {
    return <p className="loading">No tasks to display</p>;
  }

  return (
    <div className="gantt-wrap">
      <p className="gantt-hint">Click a task name or bar to open documentation</p>
      <div className="gantt-chart-row" style={{ height }}>
        <div className="gantt-labels-col" aria-label="Tasks">
          {tasks.map((t) => (
            <button
              key={t.id}
              type="button"
              className="gantt-task-label"
              style={{ borderLeftColor: barColor(t.status) }}
              onClick={() => selectTask(t)}
              title="Click to edit"
            >
              {t.task}
            </button>
          ))}
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
      </div>
    </div>
  );
}
