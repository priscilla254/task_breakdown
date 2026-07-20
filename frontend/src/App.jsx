import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  appendTaskLog,
  createTask,
  deleteTask,
  fetchTasks,
  fetchTrainingModuleTasks,
  fetchTrainingModules,
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
import {
  buildTrainingModuleSummary,
  filterTrainingModules,
  getTrainingFilterOptions,
  getTrainingHourStats,
  normalizeTrainingFilterOptions,
} from "./trainingUtils";
import StatDaysPill from "./StatDaysPill";
import TaskEditor from "./TaskEditor";
import TaskLogView from "./TaskLogView";
import AddTaskModal from "./AddTaskModal";

function mergeTasksById(existing, incoming) {
  const byId = new Map(existing.map((t) => [t.id, t]));
  for (const t of incoming) byId.set(t.id, t);
  return [...byId.values()];
}

function statsFromTasks(tasks) {
  const hs = getTrainingHourStats(tasks);
  return {
    total_effort_days: hs.totalEffortDays,
    remaining_days: hs.remainingDays,
    project_end: hs.projectEnd,
    task_count: tasks.length,
  };
}
export default function App() {
  const [activeProject, setActiveProject] = useState(DEFAULT_PROJECT_ID);
  const [tasks, setTasks] = useState([]);
  const [trainingModules, setTrainingModules] = useState([]);
  const [trainingStats, setTrainingStats] = useState(null);
  const [trainingFilterOptions, setTrainingFilterOptions] = useState(null);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [projectStart, setProjectStart] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState("gantt");
  const [logTask, setLogTask] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showAddTask, setShowAddTask] = useState(false);

  const projectMeta = getProject(activeProject);
  const isTraining = activeProject === "training";

  const filterOptionsForHook = useMemo(() => {
    if (!trainingFilterOptions) return null;
    return normalizeTrainingFilterOptions({
      ...trainingFilterOptions,
      total_tasks: trainingStats?.task_count ?? trainingFilterOptions.total_tasks,
    });
  }, [trainingFilterOptions, trainingStats]);

  const trainingFilters = useTrainingFilters(tasks, isTraining, filterOptionsForHook);
  const statusFilter = useStatusFilter(tasks, !isTraining);
  const tasksRequestRef = useRef(0);

  const filteredModules = useMemo(
    () => (isTraining ? filterTrainingModules(trainingModules, trainingFilters.filters) : []),
    [isTraining, trainingModules, trainingFilters.filters]
  );

  const needsTaskSliceForFilters =
    trainingFilters.filters.phase !== "all" ||
    trainingFilters.filters.assignee !== "all";

  const filteredDisplayCount = useMemo(() => {
    if (!isTraining) return 0;
    if (tasks.length > 0 || needsTaskSliceForFilters) {
      return trainingFilters.filteredCount;
    }
    return filteredModules.reduce((sum, m) => sum + (m.step_count || 0), 0);
  }, [
    isTraining,
    tasks.length,
    needsTaskSliceForFilters,
    trainingFilters.filteredCount,
    filteredModules,
  ]);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (activeProject === "training") {
        const data = await fetchTrainingModules();
        setTrainingModules(data.modules);
        setTrainingStats(data.stats);
        setTrainingFilterOptions(data.filter_options);
        setProjectStart(data.project_start);
        setTasks([]);
      } else {
        const taskData = await fetchTasks(activeProject);
        setTasks(taskData.tasks);
        setProjectStart(taskData.project_start);
        setTrainingModules([]);
        setTrainingStats(null);
        setTrainingFilterOptions(null);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [activeProject]);

  const loadTrainingDetailTasks = useCallback(async (filters) => {
    const requestId = ++tasksRequestRef.current;
    try {
      setTasksLoading(true);
      const params = {};
      if (filters.department !== "all") params.department = filters.department;
      if (filters.subject !== "all") params.subject = filters.subject;
      const data = await fetchTrainingModuleTasks(params);
      if (requestId !== tasksRequestRef.current) return;
      setTasks(data.tasks);
    } catch (e) {
      if (requestId !== tasksRequestRef.current) return;
      alert(e.message);
    } finally {
      if (requestId === tasksRequestRef.current) setTasksLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  useEffect(() => {
    if (!isTraining || loading) return;
    const onDetailView = view !== "overview";
    if (!onDetailView && !needsTaskSliceForFilters) return;
    loadTrainingDetailTasks(trainingFilters.filters);
  }, [
    isTraining,
    loading,
    view,
    needsTaskSliceForFilters,
    trainingFilters.filters.phase,
    trainingFilters.filters.department,
    trainingFilters.filters.subject,
    trainingFilters.filters.assignee,
    loadTrainingDetailTasks,
  ]);

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
    if (projectId === "training") setView("overview");
  };

  const applyScheduleResponse = useCallback(
    (result) => {
      if (result?.tasks) {
        setTasks(result.tasks);
        if (activeProject === "training") {
          setTrainingModules(buildTrainingModuleSummary(result.tasks));
          const stats = statsFromTasks(result.tasks);
          setTrainingStats(stats);
          setTrainingFilterOptions({
            ...getTrainingFilterOptions(result.tasks),
            total_tasks: stats.task_count,
          });
        }
      }
      if (result?.project_start) setProjectStart(result.project_start);
    },
    [activeProject]
  );

  const handleProjectStart = async (value) => {
    try {
      const result = await updateProjectStart(activeProject, value);
      applyScheduleResponse(result);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleTaskUpdate = async (id, payload) => {
    try {
      const result = await updateTask(activeProject, id, payload);
      applyScheduleResponse(result);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleTaskReorder = async (order) => {
    try {
      const result = await reorderTasks(activeProject, order);
      applyScheduleResponse(result);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleAppendLog = async (id, message) => {
    const result = await appendTaskLog(activeProject, id, message);
    applyScheduleResponse(result);
    return result.task;
  };

  const handleLogDelay = async (id, days, reason) => {
    const result = await logTaskDelay(activeProject, id, days, reason);
    applyScheduleResponse(result);
    return result;
  };

  const openLog = (task) => setLogTask(task);
  const openEditor = (task) => setEditingTask(task);

  const handleModuleSelect = useCallback(
    async (moduleIndex) => {
      try {
        const data = await fetchTrainingModuleTasks({ module_index: moduleIndex });
        setTasks((prev) => mergeTasksById(prev, data.tasks));
        const mod = trainingModules.find((m) => m.module_index === moduleIndex);
        const repId = mod?.representative_task_id ?? mod?.representativeTask?.id;
        const task = data.tasks.find((t) => t.id === repId) || data.tasks[0];
        if (task) setLogTask(task);
      } catch (e) {
        alert(e.message);
      }
    },
    [trainingModules]
  );

  const handleCreateTask = async (payload) => {
    const result = await createTask(activeProject, payload);
    applyScheduleResponse(result);
  };

  const handleDeleteTask = async (task) => {
    if (!confirmDeleteTask(task, tasks)) return;
    try {
      const result = await deleteTask(activeProject, task.id);
      if (logTask?.id === task.id) setLogTask(null);
      if (editingTask?.id === task.id) setEditingTask(null);
      applyScheduleResponse(result);
    } catch (e) {
      alert(e.message);
    }
  };

  const trainingHours = isTraining
    ? trainingStats
      ? {
          totalEffortDays: trainingStats.total_effort_days,
          remainingDays: trainingStats.remaining_days,
          projectEnd: trainingStats.project_end,
        }
      : getTrainingHourStats(tasks)
    : null;
  const projectEnd = isTraining
    ? trainingHours?.projectEnd || "—"
    : tasks.length
      ? tasks.reduce((latest, t) => {
          const end = (t.end || "").slice(0, 10);
          return end > latest ? end : latest;
        }, "")
      : "—";
  const taskCount = isTraining
    ? trainingStats?.task_count ?? tasks.length
    : tasks.length;
  const totalDays = tasks.reduce((s, t) => s + (t.days || 0), 0);
  const remainingDays = getRemainingDays(tasks);

  if (loading) {
    return (
      <div className="app-shell loading">
        Loading project schedule…
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
              <strong>{taskCount}</strong> tasks
            </span>
            {isTraining && trainingHours ? (
              <>
                <StatDaysPill
                  days={trainingHours.totalEffortDays}
                  label="total effort days"
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
                <a
                  className="btn btn-ghost"
                  href={`/api/export/html?project=${activeProject}`}
                >
                  Download HTML
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
              {isTraining ? (
                trainingModules.length === 0 ? (
                  <p className="empty-state">
                    No modules yet for this project. Use <strong>+ Add task</strong> to build your
                    breakdown.
                  </p>
                ) : (
                <div className="training-view-panel">
                  <TrainingFiltersBar
                    filters={trainingFilters.filters}
                    setFilter={trainingFilters.setFilter}
                    clearFilters={trainingFilters.clearFilters}
                    options={trainingFilters.options}
                    subjectChoices={trainingFilters.subjectChoices}
                    anyActive={trainingFilters.anyActive}
                    filteredCount={filteredDisplayCount}
                    totalCount={trainingFilters.totalCount}
                  />
                  {view === "overview" ? (
                    <TrainingModuleGantt
                      modules={filteredModules}
                      onModuleSelect={handleModuleSelect}
                      filtersActive={trainingFilters.anyActive}
                    />
                  ) : tasksLoading ? (
                    <p className="loading">Loading tasks…</p>
                  ) : trainingFilters.filteredTasks.length === 0 ? (
                    <p className="empty-state">
                      No tasks match these filters. Try clearing filters.
                    </p>
                  ) : view === "gantt" ? (
                    <GanttChart
                      tasks={trainingFilters.filteredTasks}
                      onTaskSelect={openLog}
                      trainingMode
                      filtersActive={trainingFilters.anyActive}
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
                )
              ) : tasks.length === 0 ? (
                <p className="empty-state">
                  No tasks yet for this project. Use <strong>+ Add task</strong> to build your
                  breakdown.
                </p>
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
