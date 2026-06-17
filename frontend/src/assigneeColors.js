/** Stable colour per assignee name (shared by Gantt bars and labels). */

const ASSIGNEE_HUES = [185, 160, 200, 140, 45, 280];

export const PHASE_BAR_COLORS = {
  content: "#4dd4a8",
  development: "#32c3e2",
  upload: "#c495ff",
  other: "#7a8d9c",
};

export const PRISCILLA_BORDER = "#32c3e2";
export const UNASSIGNED_BORDER = "#e8a855";

export function assigneeColor(name) {
  if (!name || !String(name).trim()) return null;
  const text = String(name).trim();
  let h = 0;
  for (let i = 0; i < text.length; i++) h = text.charCodeAt(i) + ((h << 5) - h);
  return `hsl(${ASSIGNEE_HUES[Math.abs(h) % ASSIGNEE_HUES.length]}, 55%, 58%)`;
}

export function phaseBarColor(phase) {
  return PHASE_BAR_COLORS[phase] || PHASE_BAR_COLORS.other;
}

export function trainingRowAssigneeClass(assignee) {
  const name = (assignee || "").trim();
  if (!name) return "training-assignee-unassigned";
  if (name.toLowerCase() === "priscilla") return "training-assignee-priscilla";
  return "training-assignee-other";
}

export function trainingRowAssigneeBorder(assignee) {
  const name = (assignee || "").trim();
  if (!name) return UNASSIGNED_BORDER;
  if (name.toLowerCase() === "priscilla") return PRISCILLA_BORDER;
  return assigneeColor(name);
}

export function uniqueAssignees(tasks) {
  const names = new Set();
  for (const t of tasks) {
    const a = (t.assignee || "").trim();
    if (a) names.add(a);
  }
  return [...names].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

export function taskBarColor(task, statusColors, status) {
  const assignee = (task.assignee || "").trim();
  if (assignee) return assigneeColor(assignee);
  return statusColors[status] || statusColors["Not started"];
}
