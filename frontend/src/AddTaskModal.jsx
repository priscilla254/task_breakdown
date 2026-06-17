import { useState } from "react";

const STATUSES = ["Not started", "In progress", "Completed"];

export default function AddTaskModal({ onCreate, onClose, trainingMode = false }) {
  const [task, setTask] = useState("");
  const [days, setDays] = useState(1);
  const [dependsOn, setDependsOn] = useState("");
  const [department, setDepartment] = useState("");
  const [subject, setSubject] = useState("");
  const [assignee, setAssignee] = useState("");
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
      const payload = {
        task: task.trim(),
        days: parseInt(days, 10) || 1,
        depends_on,
        status,
      };
      if (trainingMode) {
        if (department.trim()) payload.department = department.trim();
        if (subject.trim()) payload.subject = subject.trim();
      }
      if (assignee.trim()) payload.assignee = assignee.trim();
      await onCreate(payload);
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
            Duration (work days)
            <input
              type="number"
              step="1"
              min="1"
              value={days}
              onChange={(e) => setDays(e.target.value)}
              required
            />
          </label>
          <label>
            Assignee
            <input
              type="text"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              placeholder="Who is working on this"
            />
          </label>
          {trainingMode ? (
            <>
              <label>
                Department
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Group"
                />
              </label>
              <label>
                Subject
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Communications"
                />
              </label>
            </>
          ) : null}
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

