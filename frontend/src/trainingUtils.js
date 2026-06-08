/** Sort and group helpers for the training project (department → subject → task). */

const PHASE_ORDER = { content: 0, development: 1 };

export function sortTrainingTasks(tasks) {
  return [...tasks].sort((a, b) => {
    const dept = (a.department || "").localeCompare(b.department || "", undefined, {
      sensitivity: "base",
    });
    if (dept !== 0) return dept;
    const sub = (a.subject || "").localeCompare(b.subject || "", undefined, {
      sensitivity: "base",
    });
    if (sub !== 0) return sub;
    const modA = a.module_index ?? a.id;
    const modB = b.module_index ?? b.id;
    if (modA !== modB) return modA - modB;
    const phaseA = PHASE_ORDER[a.phase] ?? 2;
    const phaseB = PHASE_ORDER[b.phase] ?? 2;
    if (phaseA !== phaseB) return phaseA - phaseB;
    return a.id - b.id;
  });
}

/** Flat list of table rows: department header, subject header, then tasks. */
export function buildTrainingTableRows(tasks) {
  const sorted = sortTrainingTasks(tasks);
  const rows = [];
  let lastDept = null;
  let lastSubject = null;

  for (const task of sorted) {
    const dept = task.department || "—";
    const sub = task.subject || "—";
    if (dept !== lastDept) {
      rows.push({ type: "department", key: `dept-${dept}`, label: dept });
      lastDept = dept;
      lastSubject = null;
    }
    if (sub !== lastSubject) {
      rows.push({ type: "subject", key: `sub-${dept}-${sub}`, label: sub });
      lastSubject = sub;
    }
    rows.push({ type: "task", task });
  }
  return rows;
}

export function ganttTaskLabel(task) {
  const parts = [];
  if (task.department) parts.push(task.department);
  if (task.subject) parts.push(task.subject);
  parts.push(task.task);
  return parts.join(" › ");
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, undefined, { sensitivity: "base" })
  );
}

/** Distinct filter values from the current task list. */
export function getTrainingFilterOptions(tasks) {
  const departments = uniqueSorted(tasks.map((t) => t.department));
  const subjects = uniqueSorted(tasks.map((t) => t.subject));
  const assignees = uniqueSorted(tasks.map((t) => t.assignee));
  const subjectsByDepartment = {};
  for (const t of tasks) {
    const dept = t.department || "";
    if (!dept) continue;
    if (!subjectsByDepartment[dept]) subjectsByDepartment[dept] = new Set();
    if (t.subject) subjectsByDepartment[dept].add(t.subject);
  }
  for (const dept of Object.keys(subjectsByDepartment)) {
    subjectsByDepartment[dept] = [...subjectsByDepartment[dept]].sort((a, b) =>
      a.localeCompare(b, undefined, { sensitivity: "base" })
    );
  }
  return { departments, subjects, assignees, subjectsByDepartment };
}

export const EMPTY_TRAINING_FILTERS = {
  phase: "all",
  department: "all",
  subject: "all",
  assignee: "all",
};

import { getRemainingHours } from "./projectStats";

export function getTrainingHourStats(tasks) {
  const totalProjectHours = tasks.reduce((s, t) => s + (Number(t.hours) || 0), 0);
  const developmentHours = tasks
    .filter((t) => t.phase === "development")
    .reduce((s, t) => s + (Number(t.hours) || 0), 0);
  return {
    totalProjectHours,
    developmentHours,
    remainingHours: getRemainingHours(tasks),
  };
}

export function filterTrainingTasks(tasks, filters) {
  const { phase, department, subject, assignee } = filters;
  return tasks.filter((t) => {
    if (phase !== "all" && t.phase !== phase) return false;
    if (department !== "all" && (t.department || "") !== department) return false;
    if (subject !== "all" && (t.subject || "") !== subject) return false;
    if (assignee === "unassigned") {
      if (t.assignee && String(t.assignee).trim()) return false;
    } else if (assignee !== "all" && (t.assignee || "") !== assignee) {
      return false;
    }
    return true;
  });
}
