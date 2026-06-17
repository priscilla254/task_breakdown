import { useEffect, useState } from "react";

function statusClass(status) {
  if (status === "In progress") return "status-in-progress";
  if (status === "Completed") return "status-completed";
  return "status-not-started";
}

export default function TaskLogView({
  task,
  onAppendLog,
  onLogDelay,
  onUpdate,
  onDelete,
  onClose,
}) {
  const [logHistory, setLogHistory] = useState("");
  const [newLogEntry, setNewLogEntry] = useState("");
  const [addingLog, setAddingLog] = useState(false);
  const [delayDays, setDelayDays] = useState("");
  const [delayReason, setDelayReason] = useState("");
  const [loggingDelay, setLoggingDelay] = useState(false);
  const [lastProjectEnd, setLastProjectEnd] = useState(null);

  useEffect(() => {
    if (!task) return;
    setLogHistory(task.log || "");
  }, [task?.log, task?.delay_days, task?.delays]);

  useEffect(() => {
    if (!task) return;
    setNewLogEntry("");
    setDelayDays("");
    setDelayReason("");
    setLastProjectEnd(null);
  }, [task?.id]);

  if (!task) return null;

  const totalDelay = task.delay_days || 0;
  const effectiveDays = (task.days || 0) + totalDelay;
  const delayEntries = task.delays || [];

  const handleAddLog = async (e) => {
    e.preventDefault();
    if (!newLogEntry.trim()) return;
    setAddingLog(true);
    try {
      const updated = await onAppendLog(task.id, newLogEntry.trim());
      setLogHistory(updated.log || "");
      setNewLogEntry("");
    } catch (err) {
      alert(err.message || "Could not add log entry");
    } finally {
      setAddingLog(false);
    }
  };

  const handleLogDelay = async (e) => {
    e.preventDefault();
    const days = parseInt(delayDays, 10);
    if (!days || days < 1) {
      alert("Enter delay of at least 1 day.");
      return;
    }
    if (!delayReason.trim()) {
      alert("Enter a reason for the delay.");
      return;
    }
    setLoggingDelay(true);
    try {
      const result = await onLogDelay(task.id, days, delayReason.trim());
      setLogHistory(result.task.log || "");
      setDelayDays("");
      setDelayReason("");
      if (result.project_end) {
        setLastProjectEnd(result.project_end);
      }
    } catch (err) {
      alert(err.message || "Could not log delay");
    } finally {
      setLoggingDelay(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleAddLog(e);
    }
  };

  const delayAmount = (entry) => entry.days ?? entry.hours;

  return (
    <div className="task-log-page" role="dialog" aria-labelledby="task-log-title">
      <header className="task-log-header">
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          ← Back to timeline
        </button>
        <div className="task-log-header-actions">
          <button type="button" className="btn btn-ghost" onClick={() => onUpdate(task)}>
            Update
          </button>
          <button type="button" className="btn btn-danger" onClick={() => onDelete(task)}>
            Delete
          </button>
        </div>
      </header>

      <div className="task-log-body">
        <div className="task-log-intro">
          <h1 id="task-log-title">Task documentation</h1>
          <p className="task-log-task-name">{task.task}</p>
          <div className="task-log-meta-row">
            <span className={`status-badge ${statusClass(task.status)}`}>{task.status}</span>
            {task.department ? <span>{task.department}</span> : null}
            {task.subject ? <span>{task.subject}</span> : null}
            {task.assignee ? (
              <span className="assignee-pill">{task.assignee}</span>
            ) : null}
            <span>
              {task.start} → {(task.end || "").slice(0, 10)}
            </span>
            <span>
              {task.days}d planned
              {totalDelay > 0 ? ` + ${totalDelay}d delay = ${effectiveDays}d` : ""}
            </span>
          </div>
        </div>

        <section className="task-log-delay-section" aria-labelledby="delay-heading">
          <h2 id="delay-heading">Log delay</h2>
          <p className="task-log-delay-hint">
            Adds work days to this task and pushes dependent tasks. The project target end
            date updates when this task (or work downstream) defines the finish.
          </p>
          {lastProjectEnd && (
            <p className="task-log-delay-success" role="status">
              Project target end is now <strong>{lastProjectEnd}</strong>.
            </p>
          )}
          <form onSubmit={handleLogDelay} className="task-log-delay-form">
            <label className="task-log-delay-field">
              Delay (work days)
              <input
                type="number"
                min="1"
                step="1"
                value={delayDays}
                onChange={(e) => setDelayDays(e.target.value)}
                placeholder="e.g. 2"
                required
              />
            </label>
            <label className="task-log-delay-field task-log-delay-field-wide">
              Reason
              <input
                type="text"
                value={delayReason}
                onChange={(e) => setDelayReason(e.target.value)}
                placeholder="What caused the slip?"
                required
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={loggingDelay}>
              {loggingDelay ? "Applying…" : "Log delay & update timeline"}
            </button>
          </form>
          {delayEntries.length > 0 && (
            <ul className="task-log-delay-list">
              {delayEntries.map((entry, i) => (
                <li key={`${entry.date}-${delayAmount(entry)}-${i}`}>
                  <span className="task-log-delay-list-date">{entry.date}</span>
                  <span className="task-log-delay-list-hours">+{delayAmount(entry)}d</span>
                  <span>{entry.reason}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="task-log-compose-section" aria-labelledby="compose-heading">
          <h2 id="compose-heading">New entry</h2>
          <form onSubmit={handleAddLog} className="task-log-compose-form">
            <textarea
              className="task-log-compose-input"
              value={newLogEntry}
              onChange={(e) => setNewLogEntry(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="What happened, decisions made, blockers, next steps…"
              rows={8}
            />
            <div className="task-log-compose-actions">
              <button type="submit" className="btn btn-primary" disabled={addingLog}>
                {addingLog ? "Saving…" : "Add log entry"}
              </button>
            </div>
          </form>
        </section>

        <section className="task-log-history-section" aria-labelledby="history-heading">
          <h2 id="history-heading">History</h2>
          <pre className="task-log-history-full">
            {logHistory.trim() || "No entries yet."}
          </pre>
        </section>
      </div>
    </div>
  );
}
