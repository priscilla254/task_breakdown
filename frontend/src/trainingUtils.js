/** Sort and group helpers for the training project (department → subject → task). */

const PHASE_ORDER = { content: 0, development: 1, upload: 2 };

function stepSortKey(stepId) {
  if (!stepId) return [99, 99];
  const parts = String(stepId).split(".");
  return [parseInt(parts[0], 10) || 99, parseInt(parts[1], 10) || 99];
}

function compareStepId(a, b) {
  const [a1, a2] = stepSortKey(a.step_id);
  const [b1, b2] = stepSortKey(b.step_id);
  if (a1 !== b1) return a1 - b1;
  return a2 - b2;
}
const PARENT_PHASE_LABEL = {
  content: "Module content",
  development: "Module development",
  upload: "Module upload",
};
const MS_PER_DAY = 24 * 60 * 60 * 1000;

function defaultTrainingCompare(a, b) {
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
  const phaseA = PHASE_ORDER[a.phase] ?? 99;
  const phaseB = PHASE_ORDER[b.phase] ?? 99;
  if (phaseA !== phaseB) return phaseA - phaseB;
  const stepCmp = compareStepId(a, b);
  if (stepCmp !== 0) return stepCmp;
  return a.id - b.id;
}

export function subjectKey(task) {
  return `${task.department || ""}\0${task.subject || ""}`;
}

export function sortTrainingTasks(tasks) {
  const hasCustomOrder = tasks.some((t) => t.display_order != null);
  if (!hasCustomOrder) {
    return [...tasks].sort(defaultTrainingCompare);
  }
  return [...tasks].sort((a, b) => {
    const oa = a.display_order ?? Number.MAX_SAFE_INTEGER;
    const ob = b.display_order ?? Number.MAX_SAFE_INTEGER;
    if (oa !== ob) return oa - ob;
    return defaultTrainingCompare(a, b);
  });
}

/** Subject blocks for drag-and-drop (tasks only, in display order). */
export function buildTrainingSubjectSections(tasks) {
  const sorted = sortTrainingTasks(tasks);
  const sections = [];
  for (const task of sorted) {
    const key = subjectKey(task);
    const last = sections[sections.length - 1];
    if (last && last.key === key) {
      last.tasks.push(task);
    } else {
      sections.push({
        key,
        department: task.department || "—",
        subject: task.subject || "—",
        departmentRaw: task.department || "",
        subjectRaw: task.subject || "",
        tasks: [task],
      });
    }
  }
  for (const section of sections) {
    section.groups = buildTrainingParentGroups(section.tasks);
  }
  return sections;
}

function toDate(value) {
  if (!value) return null;
  const dt = new Date(String(value).slice(0, 10));
  return Number.isNaN(dt.getTime()) ? null : dt;
}

function calendarSpanDays(children) {
  let minStart = null;
  let maxEnd = null;
  for (const child of children) {
    const start = toDate(child.start);
    const end = toDate(child.end);
    if (!start || !end) continue;
    if (!minStart || start < minStart) minStart = start;
    if (!maxEnd || end > maxEnd) maxEnd = end;
  }
  if (!minStart || !maxEnd) {
    return children.reduce((sum, child) => sum + (Number(child.days) || 0), 0);
  }
  return Math.max(1, Math.round((maxEnd - minStart) / MS_PER_DAY) + 1);
}

function buildTrainingParentGroups(tasks) {
  const groups = [];
  const byKey = new Map();
  for (const task of tasks) {
    const rawPhase = (task.phase || "").toLowerCase();
    const phase = PARENT_PHASE_LABEL[rawPhase] ? rawPhase : "other";
    const moduleIdx = task.module_index ?? task.id;
    const key = `${moduleIdx}::${phase}`;
    let group = byKey.get(key);
    if (!group) {
      group = {
        key,
        moduleIndex: moduleIdx,
        phase,
        label: PARENT_PHASE_LABEL[phase] || "Module step",
        children: [],
      };
      byKey.set(key, group);
      groups.push(group);
    }
    group.children.push(task);
  }
  for (const group of groups) {
    group.spanDays = calendarSpanDays(group.children);
  }
  return groups;
}

/** Replace one subject block in the global id list after a within-subject drag. */
export function mergeSubjectReorder(allTasks, department, subject, newSubjectOrderIds) {
  const sorted = sortTrainingTasks(allTasks);
  const targetKey = `${department || ""}\0${subject || ""}`;
  const result = [];
  let i = 0;
  while (i < sorted.length) {
    const t = sorted[i];
    if (subjectKey(t) === targetKey) {
      while (i < sorted.length && subjectKey(sorted[i]) === targetKey) {
        i++;
      }
      result.push(...newSubjectOrderIds);
    } else {
      result.push(t.id);
      i++;
    }
  }
  return result;
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

/** Extract module title from "Module name - step" task string. */
export function moduleNameFromTask(task) {
  const text = task.task || "";
  const sep = text.indexOf(" - ");
  return sep >= 0 ? text.slice(0, sep) : text;
}

/** One row per module: span from first child start to last child end. */
export function buildTrainingModuleSummary(tasks) {
  const byModule = new Map();
  for (const t of tasks) {
    const mi = t.module_index;
    if (mi == null) continue;
    let row = byModule.get(mi);
    if (!row) {
      row = {
        module_index: mi,
        moduleName: moduleNameFromTask(t),
        department: t.department || "",
        subject: t.subject || "",
        start: t.start,
        end: t.end,
        stepCount: 0,
        representativeTask: t,
      };
      byModule.set(mi, row);
    }
    row.stepCount += 1;
    if (t.start && (!row.start || t.start < row.start)) row.start = t.start;
    if (t.end && (!row.end || t.end > row.end)) row.end = t.end;
    if (t.step_id === "3.3") row.representativeTask = t;
    else if (t.step_id === "1.1" && row.representativeTask?.step_id !== "3.3") {
      row.representativeTask = t;
    }
  }
  return [...byModule.values()]
    .sort((a, b) => a.module_index - b.module_index)
    .map((row) => {
      const startDt = toDate(row.start);
      const endDt = toDate(row.end);
      const spanDays =
        startDt && endDt
          ? Math.max(1, Math.round((endDt - startDt) / MS_PER_DAY) + 1)
          : 0;
      return {
        ...row,
        spanDays,
        label: `M${row.module_index} · ${row.moduleName}`,
      };
    });
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

import { getRemainingDays } from "./projectStats";

export function getTrainingHourStats(tasks) {
  const totalEffortDays = tasks.reduce((s, t) => s + (Number(t.days) || 0), 0);
  const developmentDays = tasks
    .filter((t) => t.phase === "development")
    .reduce((s, t) => s + (Number(t.days) || 0), 0);

  const projectEnd = tasks.reduce((latest, t) => {
    const end = (t.end || "").slice(0, 10);
    return end > latest ? end : latest;
  }, "");

  let calendarSpanDays = 0;
  if (projectEnd) {
    const ends = tasks
      .map((t) => toDate(t.end))
      .filter(Boolean);
    const starts = tasks
      .map((t) => toDate(t.start))
      .filter(Boolean);
    if (ends.length && starts.length) {
      const minStart = new Date(Math.min(...starts.map((d) => d.getTime())));
      const maxEnd = new Date(Math.max(...ends.map((d) => d.getTime())));
      calendarSpanDays = Math.max(
        1,
        Math.round((maxEnd - minStart) / MS_PER_DAY) + 1
      );
    }
  }

  return {
    totalProjectDays: totalEffortDays,
    totalEffortDays,
    developmentDays,
    remainingDays: getRemainingDays(tasks),
    projectEnd,
    calendarSpanDays,
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
