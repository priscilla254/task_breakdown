import { useEffect, useState } from "react";

const STATUSES = ["Not started", "In progress", "Completed"];

export default function TaskEditor({ task, onSave, onClose }) {
  const [status, setStatus] = useState("Not started");
  const [hours, setHours] = useState(0);
  const [startDate, setStartDate] = useState("");
  const [useAutoStart, setUseAutoStart] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!task) return;
    setStatus(task.status || "Not started");
    setHours(task.hours ?? 0);
    setStartDate(task.fixed_start || task.start || "");
    setUseAutoStart(!task.fixed_start);
  }, [task]);

  if (!task) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(task.id, {
        status,
        hours: parseFloat(hours),
        fixed_start: useAutoStart ? null : startDate,
      });
      onClose();
    } catch (err) {
      alert(err.message || "Save failed");
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
        aria-labelledby="task-editor-title"
      >
        <div className="modal-header">
          <h2 id="task-editor-title">Edit schedule</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <p className="modal-task-name">{task.task}</p>
        <form onSubmit={handleSubmit} className="modal-form">
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
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useAutoStart}
              onChange={(e) => setUseAutoStart(e.target.checked)}
            />
            Auto-schedule start from dependencies
          </label>
          {!useAutoStart && (
            <label>
              Start date
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </label>
          )}
          {!useAutoStart && (
            <p className="modal-hint">
              Start cannot be earlier than predecessor end dates; dependent tasks will shift
              automatically.
            </p>
          )}
          <div className="modal-meta">
            <span>Scheduled: {task.start}</span>
            <span>→ {(task.end || "").slice(0, 10)}</span>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save & reschedule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
