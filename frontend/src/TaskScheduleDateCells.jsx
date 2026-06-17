import { useEffect, useState } from "react";

function commitStart(value, task, onUpdate) {
  const trimmed = (value || "").slice(0, 10) || null;
  const current = task.fixed_start || null;
  if (trimmed === current) return;
  if (!current && trimmed === (task.start || "").slice(0, 10)) return;
  onUpdate(task.id, { fixed_start: trimmed });
}

function commitEnd(value, task, onUpdate) {
  const trimmed = (value || "").slice(0, 10) || null;
  const current = task.fixed_end || null;
  if (trimmed === current) return;
  if (!current && trimmed === (task.end || "").slice(0, 10)) return;
  onUpdate(task.id, { fixed_end: trimmed });
}

export function TaskScheduleDateCells({ task, onUpdate }) {
  const manualStart = Boolean(task.fixed_start);
  const manualEnd = Boolean(task.fixed_end);
  const startDisplay = (task.fixed_start || task.start || "").slice(0, 10);
  const endDisplay = (task.fixed_end || (task.end || "").slice(0, 10));

  const [start, setStart] = useState(startDisplay);
  const [end, setEnd] = useState(endDisplay);

  useEffect(() => {
    setStart(startDisplay);
    setEnd(endDisplay);
  }, [task.id, startDisplay, endDisplay]);

  return (
    <>
      <td className="date-cell">
        <input
          type="date"
          className={`date-input${manualStart ? " date-input-manual" : ""}`}
          value={start}
          title={
            manualStart
              ? "Manual start — clear the date to auto-schedule from dependencies"
              : "Auto from dependencies — set a date to override"
          }
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            const value = e.target.value;
            setStart(value);
            commitStart(value, task, onUpdate);
          }}
        />
      </td>
      <td className="date-cell">
        <input
          type="date"
          className={`date-input${manualEnd ? " date-input-manual" : ""}`}
          value={end}
          title={
            manualEnd
              ? "Manual end — clear the date to calculate from days"
              : "Auto from days — set a date to override (e.g. parallel work)"
          }
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            const value = e.target.value;
            setEnd(value);
            commitEnd(value, task, onUpdate);
          }}
        />
      </td>
    </>
  );
}
