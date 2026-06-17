import { useMemo, useCallback, useRef, useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { assigneeColor } from "./assigneeColors";
import { buildTrainingModuleSummary } from "./trainingUtils";

const ROW_HEIGHT = 26;
const PLOT_MARGIN_TOP = 16;
const PLOT_MARGIN_BOTTOM = 40;

export default function TrainingModuleGantt({ tasks, onTaskSelect, filtersActive = false }) {
  const modules = useMemo(() => buildTrainingModuleSummary(tasks), [tasks]);

  const moduleByIndex = useMemo(() => {
    const map = new Map();
    for (const m of modules) map.set(m.module_index, m);
    return map;
  }, [modules]);

  const chartHeight =
    PLOT_MARGIN_TOP + modules.length * ROW_HEIGHT + PLOT_MARGIN_BOTTOM;

  const plotColRef = useRef(null);
  const [plotWidth, setPlotWidth] = useState(0);

  useEffect(() => {
    const el = plotColRef.current;
    if (!el) return;
    const measure = () => {
      const w = el.clientWidth;
      if (w > 0) setPlotWidth(w);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { data, layout } = useMemo(() => {
    const y = [];
    const durations = [];
    const bases = [];
    const colors = [];
    const customdata = [];

    for (const m of modules) {
      const start = new Date(m.start);
      const end = new Date(m.end);
      y.push(m.label);
      durations.push(end - start);
      bases.push(start);
      colors.push(assigneeColor(m.department) || "#32c3e2");
      customdata.push([
        m.start,
        (m.end || "").slice(0, 10),
        m.spanDays,
        m.department || "—",
        m.subject || "—",
        m.module_index,
        m.stepCount,
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
            line: { color: "rgba(255,255,255,0.15)", width: 0.5 },
          },
          customdata,
          hovertemplate:
            "<b>%{y}</b><br>Dept: %{customdata[3]}<br>Subject: %{customdata[4]}<br>" +
            "Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
            "Calendar span: %{customdata[2]} days<br>Steps: %{customdata[6]}<br>" +
            "<i>Click to open module</i><extra></extra>",
        },
      ],
      layout: {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "DM Sans, sans-serif", color: "#b8c5d0", size: 11 },
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
        margin: { l: 12, r: 24, t: PLOT_MARGIN_TOP, b: PLOT_MARGIN_BOTTOM },
        bargap: 0.12,
        autosize: false,
        showlegend: false,
        hoverlabel: {
          bgcolor: "#465667",
          bordercolor: "#32c3e2",
          font: { color: "#f4f8fb" },
        },
      },
    };
  }, [modules]);

  const selectModule = useCallback(
    (moduleIndex) => {
      const m = moduleByIndex.get(moduleIndex);
      if (m?.representativeTask && onTaskSelect) onTaskSelect(m.representativeTask);
    },
    [moduleByIndex, onTaskSelect]
  );

  const handleClick = useCallback(
    (event) => {
      const point = event?.points?.[0];
      if (!point?.customdata) return;
      selectModule(point.customdata[5]);
    },
    [selectModule]
  );

  if (!modules.length) {
    return <p className="loading">No modules to display</p>;
  }

  const lastEnd = modules.reduce(
    (latest, m) => ((m.end || "").slice(0, 10) > latest ? (m.end || "").slice(0, 10) : latest),
    ""
  );

  return (
    <div className="gantt-wrap gantt-wrap-module-overview">
      <p className="gantt-hint">
        One bar per module ({modules.length} total) from assign (1.1) through go-live (3.3). The
        staggered pipeline shows when each module enters the schedule; the last bar ends on{" "}
        <strong>{lastEnd}</strong> (matches Target end above).
        {filtersActive
          ? " Filters apply to task list and detail Gantt only — overview always shows all modules."
          : null}
      </p>
      <div
        className="gantt-chart-row gantt-chart-row-module-overview"
        style={{ height: chartHeight }}
      >
        <div className="gantt-labels-col gantt-labels-col-module-overview" aria-label="Modules">
          {modules.map((m) => (
            <button
              key={m.module_index}
              type="button"
              className="gantt-task-label gantt-task-label-module-overview"
              style={{
                borderLeftColor: assigneeColor(m.department) || "#32c3e2",
                height: ROW_HEIGHT,
                minHeight: ROW_HEIGHT,
                flex: "0 0 auto",
              }}
              onClick={() => selectModule(m.module_index)}
              title={`${m.label}\n${m.department} › ${m.subject}`}
            >
              <span className="gantt-label-text">{m.label}</span>
            </button>
          ))}
        </div>
        <div
          ref={plotColRef}
          className="gantt-plot-col gantt-plot-col-module-overview"
          style={{ height: chartHeight }}
        >
          {plotWidth > 0 ? (
            <Plot
              data={data}
              layout={{ ...layout, width: plotWidth, height: chartHeight }}
              config={{ responsive: false, displayModeBar: true, displaylogo: false }}
              style={{ width: plotWidth, height: chartHeight, cursor: "pointer" }}
              onClick={handleClick}
            />
          ) : null}
        </div>
      </div>
      <div className="legend">
        <span className="legend-item legend-hint">Bar colour = department</span>
        <span className="legend-item legend-hint">Click a row to open that module</span>
      </div>
    </div>
  );
}
