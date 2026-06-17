import { useEffect, useState } from "react";

const STATUSES = ["Not started", "In progress", "Completed"];

export default function TaskEditor({ task, onSave, onDelete, onClose, trainingMode = false }) {
  const [name, setName] = useState("");
  const [status, setStatus] = useState("Not started");
  const [days, setDays] = useState(1);
  const [department, setDepartment] = useState("");
  const [subject, setSubject] = useState("");
  const [assignee, setAssignee] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [useAutoStart, setUseAutoStart] = useState(true);
  const [useAutoEnd, setUseAutoEnd] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!task) return;
    setName(task.task || "");
    setStatus(task.status || "Not started");
    setDays(task.days ?? 1);
    setDepartment(task.department || "");
    setSubject(task.subject || "");
    setAssignee(task.assignee || "");
    setStartDate(task.fixed_start || task.start || "");
    setEndDate(task.fixed_end || (task.end || "").slice(0, 10) || "");
    setUseAutoStart(!task.fixed_start);
    setUseAutoEnd(!task.fixed_end);
  }, [task]);

  if (!task) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      alert("Task name is required.");
      return;
    }
    if (!useAutoEnd && !useAutoStart && endDate && startDate && endDate < startDate) {
      alert("End date cannot be before start date.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        task: trimmed,
        status,
        days: parseInt(days, 10) || 1,
        fixed_start: useAutoStart ? null : startDate,
        fixed_end: useAutoEnd ? null : endDate,
        assignee: assignee.trim(),
      };
      if (trainingMode) {
        payload.department = department.trim();
        payload.subject = subject.trim();
      }
      await onSave(task.id, payload);
      onClose();
    } catch (err) {
      alert(err.message || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await onDelete(task);
      onClose();
    } finally {
      setDeleting(false);
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
          <h2 id="task-editor-title">Update task</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <label>
            Task name
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
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
                  placeholder="e.g. Group, QS"
                />
              </label>
              <label>
                Subject
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Introduction"
                />
              </label>
            </>
          ) : null}
          <label>
            Assignee
            <input
              type="text"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              placeholder="Who is working on this"
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
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useAutoEnd}
              onChange={(e) => setUseAutoEnd(e.target.checked)}
            />
            Auto-schedule end from days
          </label>
          {!useAutoEnd && (
            <label>
              End date
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </label>
          )}
          {!useAutoEnd && (
            <p className="modal-hint">
              Use a fixed end for parallel work; days still count toward project totals but do not
              set the bar length while end is manual.
            </p>
          )}
          <div className="modal-meta">
            <span>Scheduled: {task.start}</span>
            <span>→ {(task.end || "").slice(0, 10)}</span>
          </div>
          <div className="modal-actions modal-actions-spread">
            <button
              type="button"
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={deleting || saving}
            >
              {deleting ? "Deleting…" : "Delete"}
            </button>
            <div className="modal-actions-right">
              <button type="button" className="btn btn-ghost" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving || deleting}>
                {saving ? "Updating…" : "Update"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
