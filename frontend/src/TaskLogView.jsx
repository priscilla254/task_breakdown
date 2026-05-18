import { useEffect, useState } from "react";

function statusClass(status) {
  if (status === "In progress") return "status-in-progress";
  if (status === "Completed") return "status-completed";
  return "status-not-started";
}

export default function TaskLogView({ task, onAppendLog, onEditSchedule, onClose }) {
  const [logHistory, setLogHistory] = useState("");
  const [newLogEntry, setNewLogEntry] = useState("");
  const [addingLog, setAddingLog] = useState(false);

  useEffect(() => {
    if (!task) return;
    setLogHistory(task.log || "");
    setNewLogEntry("");
  }, [task]);

  if (!task) return null;

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

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleAddLog(e);
    }
  };

  return (
    <div className="task-log-page" role="dialog" aria-labelledby="task-log-title">
      <header className="task-log-header">
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          ← Back to timeline
        </button>
        <div className="task-log-header-actions">
          <button type="button" className="btn btn-ghost" onClick={() => onEditSchedule(task)}>
            Edit schedule
          </button>
        </div>
      </header>

      <div className="task-log-body">
        <div className="task-log-intro">
          <h1 id="task-log-title">Task documentation</h1>
          <p className="task-log-task-name">{task.task}</p>
          <div className="task-log-meta-row">
            <span className={`status-badge ${statusClass(task.status)}`}>
              {task.status}
            </span>
            <span>
              {task.start} → {(task.end || "").slice(0, 10)}
            </span>
            <span>{task.hours} project hours</span>
          </div>
        </div>

        <section className="task-log-compose-section" aria-labelledby="compose-heading">
          <h2 id="compose-heading">New entry</h2>
          <form onSubmit={handleAddLog} className="task-log-compose-form">
            <textarea
              className="task-log-compose-input"
              value={newLogEntry}
              onChange={(e) => setNewLogEntry(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="What happened, decisions made, blockers, next steps…"
              rows={12}
              autoFocus
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
