import { useMemo, useCallback, useRef, useState, useEffect } from "react";
import Plot from "react-plotly.js";
import { assigneeColor } from "./assigneeColors";

const ROW_HEIGHT = 26;
const PLOT_MARGIN_TOP = 16;
const PLOT_MARGIN_BOTTOM = 40;
const MS_PER_DAY = 24 * 60 * 60 * 1000;
const X_PAD_DAYS = 21;

/** Normalize API or client module rows for the chart. */
function normalizeModule(m) {
  const rep = m.representativeTask;
  const name = m.module_name || m.moduleName || "";
  return {
    module_index: m.module_index,
    moduleName: name,
    department: m.department || "",
    subject: m.subject || "",
    start: m.start,
    end: m.end,
    spanDays: m.span_days ?? m.spanDays ?? 0,
    stepCount: m.step_count ?? m.stepCount ?? 0,
    label: m.label || `M${m.module_index} · ${name}`,
    representative_task_id: m.representative_task_id ?? rep?.id,
  };
}

export default function TrainingModuleGantt({
  modules: modulesProp,
  onModuleSelect,
  filtersActive = false,
}) {
  const modules = useMemo(
    () => (modulesProp || []).map(normalizeModule),
    [modulesProp]
  );

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
    let minTime = Infinity;
    let maxTime = -Infinity;

    for (const m of modules) {
      const start = new Date(m.start);
      const end = new Date(m.end);
      const startMs = start.getTime();
      const endMs = end.getTime();
      if (Number.isFinite(startMs)) {
        minTime = Math.min(minTime, startMs);
        maxTime = Math.max(maxTime, endMs > startMs ? endMs : startMs);
      }
      // Unique categorical key — Plotly alphabetises y labels by default (M10 before M2).
      y.push(`M${String(m.module_index).padStart(3, "0")}`);
      durations.push(Math.max(endMs - startMs, MS_PER_DAY));
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
        m.label,
      ]);
    }

    const xaxis = {
      type: "date",
      gridcolor: "rgba(50,195,226,0.12)",
      linecolor: "rgba(50,195,226,0.25)",
      tickfont: { color: "#b8c5d0" },
    };
    if (minTime < Infinity && maxTime > -Infinity) {
      xaxis.range = [
        new Date(minTime - X_PAD_DAYS * MS_PER_DAY).toISOString(),
        new Date(maxTime + X_PAD_DAYS * MS_PER_DAY).toISOString(),
      ];
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
            "<b>%{customdata[7]}</b><br>Dept: %{customdata[3]}<br>Subject: %{customdata[4]}<br>" +
            "Start: %{customdata[0]}<br>End: %{customdata[1]}<br>" +
            "Calendar span: %{customdata[2]} days<br>Steps: %{customdata[6]}<br>" +
            "<i>Click to open module</i><extra></extra>",
        },
      ],
      layout: {
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { family: "DM Sans, sans-serif", color: "#b8c5d0", size: 11 },
        xaxis,
        yaxis: {
          type: "category",
          autorange: "reversed",
          categoryorder: "array",
          categoryarray: y,
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
      if (onModuleSelect) onModuleSelect(moduleIndex);
    },
    [onModuleSelect]
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
          ? " Department and subject filters apply here; phase and assignee apply on Gantt and task list."
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
