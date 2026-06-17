import { useCallback, useEffect, useState } from "react";
import {
  appendTaskLog,
  createTask,
  deleteTask,
  fetchTasks,
  logTaskDelay,
  reorderTasks,
  updateProjectStart,
  updateTask,
} from "./api";
import { confirmDeleteTask } from "./taskActions";
import { DEFAULT_PROJECT_ID, PROJECTS, getProject } from "./projects";
import GanttChart from "./GanttChart";
import TrainingFiltersBar from "./TrainingFiltersBar";
import StatusFilterBar from "./StatusFilterBar";
import TaskTable from "./TaskTable";
import TrainingModuleGantt from "./TrainingModuleGantt";
import TrainingTaskTable from "./TrainingTaskTable";
import { useTrainingFilters } from "./useTrainingFilters";
import { useStatusFilter } from "./useStatusFilter";
import { getRemainingDays } from "./projectStats";
import { getTrainingHourStats } from "./trainingUtils";
import StatDaysPill from "./StatDaysPill";
import TaskEditor from "./TaskEditor";
import TaskLogView from "./TaskLogView";
import AddTaskModal from "./AddTaskModal";

export default function App() {
  const [activeProject, setActiveProject] = useState(DEFAULT_PROJECT_ID);
  const [tasks, setTasks] = useState([]);
  const [projectStart, setProjectStart] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState("gantt");
  const [logTask, setLogTask] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showAddTask, setShowAddTask] = useState(false);

  const projectMeta = getProject(activeProject);
  const isTraining = activeProject === "training";

  const trainingFilters = useTrainingFilters(tasks, isTraining);
  const statusFilter = useStatusFilter(tasks, !isTraining);

  const load = useCallback(async () => {
    try {
      setError(null);
      const taskData = await fetchTasks(activeProject);
      setTasks(taskData.tasks);
      setProjectStart(taskData.project_start);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [activeProject]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  useEffect(() => {
    if (!logTask) return;
    const fresh = tasks.find((t) => t.id === logTask.id);
    if (fresh) setLogTask(fresh);
  }, [tasks, logTask?.id]);

  useEffect(() => {
    if (!editingTask) return;
    const fresh = tasks.find((t) => t.id === editingTask.id);
    if (fresh) setEditingTask(fresh);
  }, [tasks, editingTask?.id]);

  const switchProject = (projectId) => {
    if (projectId === activeProject) return;
    setActiveProject(projectId);
    setLogTask(null);
    setEditingTask(null);
    setShowAddTask(false);
    setLoading(true);
    if (projectId === "training") setView("tasks");
  };

  const handleProjectStart = async (value) => {
    try {
      await updateProjectStart(activeProject, value);
      await load();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleTaskUpdate = async (id, payload) => {
    try {
      await updateTask(activeProject, id, payload);
      await load();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleTaskReorder = async (order) => {
    try {
      const result = await reorderTasks(activeProject, order);
      setTasks(result.tasks);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleAppendLog = async (id, message) => {
    const result = await appendTaskLog(activeProject, id, message);
    await load();
    return result.task;
  };

  const handleLogDelay = async (id, days, reason) => {
    const result = await logTaskDelay(activeProject, id, days, reason);
    await load();
    return result;
  };

  const openLog = (task) => setLogTask(task);
  const openEditor = (task) => setEditingTask(task);

  const handleCreateTask = async (payload) => {
    await createTask(activeProject, payload);
    await load();
  };

  const handleDeleteTask = async (task) => {
    if (!confirmDeleteTask(task, tasks)) return;
    try {
      await deleteTask(activeProject, task.id);
      if (logTask?.id === task.id) setLogTask(null);
      if (editingTask?.id === task.id) setEditingTask(null);
      await load();
    } catch (e) {
      alert(e.message);
    }
  };

  const trainingHours = isTraining ? getTrainingHourStats(tasks) : null;
  const projectEnd = isTraining && trainingHours?.projectEnd
    ? trainingHours.projectEnd
    : tasks.length
      ? tasks.reduce((latest, t) => {
          const end = (t.end || "").slice(0, 10);
          return end > latest ? end : latest;
        }, "")
      : "—";
  const totalDays = tasks.reduce((s, t) => s + (t.days || 0), 0);
  const remainingDays = getRemainingDays(tasks);

  if (loading) {
    return (
      <div className="app-shell loading">
        Loading project schedule…
        {activeProject === "training" ? " (2,500+ tasks — may take a moment)" : ""}
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-shell">
        <div className="error-banner">{error}</div>
      </div>
    );
  }

  return (
    <>
      {!logTask && (
        <div className="app-shell">
          <div
            className="project-tabs view-toggle"
            role="tablist"
            aria-label="Project"
          >
            {PROJECTS.map((p) => (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={activeProject === p.id}
                className={activeProject === p.id ? "active" : ""}
                onClick={() => switchProject(p.id)}
              >
                {p.tabLabel}
              </button>
            ))}
          </div>

          <header className="app-header">
            <div>
              <h1>
                {projectMeta.title}
                {projectMeta.highlight ? (
                  <>
                    {" "}
                    <span>{projectMeta.highlight}</span>
                  </>
                ) : null}
              </h1>
              <p>{projectMeta.subtitle}</p>
            </div>
            <div className="toolbar">
              <label>
                Project start
                <input
                  type="date"
                  value={projectStart}
                  onChange={(e) => handleProjectStart(e.target.value)}
                />
              </label>
            </div>
          </header>

          <div className="stats-row">
            <span className="stat-pill">
              <strong>{tasks.length}</strong> tasks
            </span>
            {isTraining && trainingHours ? (
              <>
                <StatDaysPill
                  days={trainingHours.calendarSpanDays}
                  label="calendar span days"
                />
                <StatDaysPill
                  days={trainingHours.totalEffortDays}
                  label="total effort days"
                />
                <StatDaysPill
                  days={trainingHours.developmentDays}
                  label="development days"
                  className="stat-pill-dev"
                />
                <StatDaysPill
                  days={trainingHours.remainingDays}
                  label="remaining days"
                  className="stat-pill-remaining"
                />
              </>
            ) : (
              <>
                <StatDaysPill days={totalDays} label="project days" />
                <StatDaysPill
                  days={remainingDays}
                  label="remaining days"
                  className="stat-pill-remaining"
                />
              </>
            )}
            <span className="stat-pill">
              Target end <strong>{projectEnd}</strong>
            </span>
          </div>

          <section className="card main-panel">
            <div className="card-header">
              <h2>
                {view === "overview"
                  ? "Module overview"
                  : view === "gantt"
                    ? "Timeline"
                    : "Tasks"}
              </h2>
              <div className="card-header-actions">
                <a
                  className="btn btn-ghost"
                  href={`/api/export?project=${activeProject}`}
                >
                  Download CSV
                </a>
                <button type="button" className="btn btn-primary" onClick={() => setShowAddTask(true)}>
                  + Add task
                </button>
                <div className="view-toggle" role="tablist" aria-label="View mode">
                  {isTraining ? (
                    <button
                      type="button"
                      role="tab"
                      aria-selected={view === "overview"}
                      className={view === "overview" ? "active" : ""}
                      onClick={() => setView("overview")}
                    >
                      Module overview
                    </button>
                  ) : null}
                  <button
                    type="button"
                    role="tab"
                    aria-selected={view === "gantt"}
                    className={view === "gantt" ? "active" : ""}
                    onClick={() => setView("gantt")}
                  >
                    Gantt chart
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={view === "tasks"}
                    className={view === "tasks" ? "active" : ""}
                    onClick={() => setView("tasks")}
                  >
                    Task list
                  </button>
                </div>
              </div>
            </div>
            <div
              className={`card-body ${view === "tasks" ? "card-body-table" : ""} ${view === "overview" ? "card-body-module-overview" : ""}`}
            >
              {tasks.length === 0 ? (
                <p className="empty-state">
                  No tasks yet for this project. Use <strong>+ Add task</strong> to build your
                  breakdown.
                </p>
              ) : isTraining ? (
                <div className="training-view-panel">
                  <TrainingFiltersBar
                    filters={trainingFilters.filters}
                    setFilter={trainingFilters.setFilter}
                    clearFilters={trainingFilters.clearFilters}
                    options={trainingFilters.options}
                    subjectChoices={trainingFilters.subjectChoices}
                    anyActive={trainingFilters.anyActive}
                    filteredCount={trainingFilters.filteredCount}
                    totalCount={trainingFilters.totalCount}
                  />
                  {view === "overview" ? (
                    <TrainingModuleGantt
                      tasks={tasks}
                      onTaskSelect={openLog}
                      filtersActive={trainingFilters.anyActive}
                    />
                  ) : trainingFilters.filteredTasks.length === 0 ? (
                    <p className="empty-state">
                      No tasks match these filters. Try clearing filters.
                    </p>
                  ) : view === "gantt" ? (
                    <GanttChart
                      tasks={trainingFilters.filteredTasks}
                      onTaskSelect={openLog}
                      trainingMode
                    />
                  ) : (
                    <TrainingTaskTable
                      tasks={trainingFilters.filteredTasks}
                      allTasks={tasks}
                      onUpdate={handleTaskUpdate}
                      onReorder={handleTaskReorder}
                      onTaskSelect={openLog}
                      onEditSchedule={openEditor}
                      onDelete={handleDeleteTask}
                      reorderEnabled={!trainingFilters.anyActive}
                    />
                  )}
                </div>
              ) : (
                <div className="phase1-view-panel">
                  <StatusFilterBar
                    filters={statusFilter.filters}
                    setFilter={statusFilter.setFilter}
                    clearFilters={statusFilter.clearFilters}
                    anyActive={statusFilter.anyActive}
                    filteredCount={statusFilter.filteredCount}
                    totalCount={statusFilter.totalCount}
                  />
                  {statusFilter.filteredTasks.length === 0 ? (
                    <p className="empty-state">
                      No tasks match this filter. Try clearing the filter.
                    </p>
                  ) : view === "gantt" ? (
                    <GanttChart tasks={statusFilter.filteredTasks} onTaskSelect={openLog} />
                  ) : (
                    <TaskTable
                      tasks={statusFilter.filteredTasks}
                      onUpdate={handleTaskUpdate}
                      onReorder={handleTaskReorder}
                      onTaskSelect={openLog}
                      onEditSchedule={openEditor}
                      onDelete={handleDeleteTask}
                      reorderEnabled={!statusFilter.anyActive}
                    />
                  )}
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      {logTask && (
        <TaskLogView
          task={logTask}
          onClose={() => setLogTask(null)}
          onAppendLog={handleAppendLog}
          onLogDelay={handleLogDelay}
          onUpdate={openEditor}
          onDelete={handleDeleteTask}
        />
      )}

      <TaskEditor
        task={editingTask}
        trainingMode={isTraining}
        onClose={() => setEditingTask(null)}
        onSave={handleTaskUpdate}
        onDelete={handleDeleteTask}
      />

      {showAddTask && (
        <AddTaskModal
          trainingMode={isTraining}
          onCreate={handleCreateTask}
          onClose={() => setShowAddTask(false)}
        />
      )}
    </>
  );
}
