import { useMemo } from "react";
import { buildTrainingTableRows } from "./trainingUtils";

function statusClass(status) {
  if (status === "In progress") return "status-in-progress";
  if (status === "Completed") return "status-completed";
  return "status-not-started";
}

export default function TrainingTaskTable({
  tasks,
  onUpdate,
  onTaskSelect,
  onEditSchedule,
  onDelete,
}) {
  const rows = useMemo(() => buildTrainingTableRows(tasks), [tasks]);

  const handleDepsBlur = (id, value) => {
    const depends_on = value.trim()
      ? value.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n))
      : [];
    onUpdate(id, { depends_on });
  };

  const handleAssigneeBlur = (id, value) => {
    onUpdate(id, { assignee: value.trim() || "" });
  };

  return (
    <div className="table-scroll">
      <table className="training-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Task</th>
            <th>Phase</th>
            <th>Assignee</th>
            <th>Deps</th>
            <th>Start</th>
            <th>End</th>
            <th>Hrs</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            if (row.type === "department") {
              return (
                <tr key={row.key} className="section-row section-row-department">
                  <td colSpan={10}>{row.label}</td>
                </tr>
              );
            }
            if (row.type === "subject") {
              return (
                <tr key={row.key} className="section-row section-row-subject">
                  <td colSpan={10}>{row.label}</td>
                </tr>
              );
            }
            const t = row.task;
            return (
              <tr
                key={t.id}
                className="task-row-clickable training-task-row"
                onClick={() => onTaskSelect?.(t)}
              >
                <td>{t.id}</td>
                <td className="task-name">{t.task}</td>
                <td>
                  <span className={`phase-badge phase-${t.phase || "other"}`}>
                    {t.phase === "development" ? "Dev" : t.phase === "content" ? "Content" : "—"}
                  </span>
                </td>
                <td>
                  <input
                    type="text"
                    className="assignee-input"
                    defaultValue={t.assignee || ""}
                    placeholder="Who"
                    onClick={(e) => e.stopPropagation()}
                    onBlur={(e) => handleAssigneeBlur(t.id, e.target.value)}
                  />
                </td>
                <td>
                  <input
                    type="text"
                    defaultValue={(t.depends_on || []).join(", ")}
                    placeholder="1, 6"
                    onClick={(e) => e.stopPropagation()}
                    onBlur={(e) => handleDepsBlur(t.id, e.target.value)}
                  />
                </td>
                <td className="date-cell">{t.start}</td>
                <td className="date-cell">{(t.end || "").slice(0, 10)}</td>
                <td>
                  <input
                    type="number"
                    step="0.5"
                    defaultValue={t.hours}
                    onClick={(e) => e.stopPropagation()}
                    onBlur={(e) => onUpdate(t.id, { hours: parseFloat(e.target.value) })}
                  />
                </td>
                <td>
                  <select
                    defaultValue={t.status}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => onUpdate(t.id, { status: e.target.value })}
                    className={`status-badge ${statusClass(t.status)}`}
                  >
                    <option>Not started</option>
                    <option>In progress</option>
                    <option>Completed</option>
                  </select>
                </td>
                <td className="table-actions-cell">
                  <button
                    type="button"
                    className="btn-table-edit"
                    title="Update task"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditSchedule?.(t);
                    }}
                  >
                    Update
                  </button>
                  <button
                    type="button"
                    className="btn-table-delete"
                    title="Delete task"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete?.(t);
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
