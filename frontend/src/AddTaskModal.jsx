import { useState } from "react";

const STATUSES = ["Not started", "In progress", "Completed"];

export default function AddTaskModal({ onCreate, onClose }) {
  const [task, setTask] = useState("");
  const [hours, setHours] = useState(8);
  const [dependsOn, setDependsOn] = useState("");
  const [status, setStatus] = useState("Not started");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!task.trim()) return;
    setSaving(true);
    try {
      const depends_on = dependsOn.trim()
        ? dependsOn.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n))
        : [];
      await onCreate({
        task: task.trim(),
        hours: parseFloat(hours),
        depends_on,
        status,
      });
      onClose();
    } catch (err) {
      alert(err.message || "Could not create task");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay modal-overlay-stacked" onClick={onClose} role="presentation">
      <div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="add-task-title"
      >
        <div className="modal-header">
          <h2 id="add-task-title">Add task</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <label>
            Task name
            <input
              type="text"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="e.g. 30. New milestone"
              required
              autoFocus
            />
          </label>
          <label>
            Duration (project hours)
            <input
              type="number"
              step="0.5"
              min="0"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              required
            />
          </label>
          <label>
            Depends on (task IDs)
            <input
              type="text"
              value={dependsOn}
              onChange={(e) => setDependsOn(e.target.value)}
              placeholder="e.g. 15, 16 or leave empty"
            />
          </label>
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <p className="modal-hint">
            A new ID is assigned automatically. Dates are calculated from dependencies and project
            start.
          </p>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Adding…" : "Add task"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

