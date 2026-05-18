function statusClass(status) {
  if (status === "In progress") return "status-in-progress";
  if (status === "Completed") return "status-completed";
  return "status-not-started";
}

export default function TaskTable({ tasks, onUpdate, onTaskSelect, onEditSchedule }) {
  const handleDepsBlur = (id, value) => {
    const depends_on = value.trim()
      ? value.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n))
      : [];
    onUpdate(id, { depends_on });
  };

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Task</th>
            <th>Deps</th>
            <th>Start</th>
            <th>End</th>
            <th>Hrs</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr
              key={t.id}
              className="task-row-clickable"
              onClick={() => onTaskSelect?.(t)}
            >
              <td>{t.id}</td>
              <td className="task-name">{t.task}</td>
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
                  onBlur={(e) =>
                    onUpdate(t.id, { hours: parseFloat(e.target.value) })
                  }
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
              <td>
                <button
                  type="button"
                  className="btn-table-edit"
                  title="Edit schedule"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEditSchedule?.(t);
                  }}
                >
                  Schedule
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


