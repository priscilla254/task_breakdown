/** Stable colour per assignee name (shared by Gantt bars and labels). */

/** Fallback hues spread around the wheel so hashed names stay distinct. */
const ASSIGNEE_HUES = [200, 25, 145, 280, 45, 330, 170, 85];

/** Fixed palette for known people / pairs (keyed by canonicalizeAssignee). */
const ASSIGNEE_COLORS = {
  priscilla: "#32c3e2", // cyan
  directors: "#e8a855", // amber
  anthony: "#7d9cff", // blue
  tdl: "#c495ff", // purple
  "directors, priscilla": "#4dd4a8", // teal-green
  "anthony, priscilla": "#f0a0c0", // pink
  "priscilla, tdl": "#9ad66a", // lime
};

export const PHASE_BAR_COLORS = {
  content: "#4dd4a8",
  development: "#32c3e2",
  upload: "#c495ff",
  other: "#7a8d9c",
};

export const PRISCILLA_BORDER = "#32c3e2";
export const UNASSIGNED_BORDER = "#e8a855";

/** Normalize "Priscilla, Directors" and "Directors, Priscilla" to one form. */
export function canonicalizeAssignee(value) {
  if (!value || !String(value).trim()) return "";
  const parts = String(value)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  if (!parts.length) return "";
  const byKey = new Map();
  for (const part of parts) {
    const key = part.toLowerCase();
    if (!byKey.has(key)) byKey.set(key, part);
  }
  return [...byKey.values()]
    .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }))
    .join(", ");
}

export function assigneeColor(name) {
  const text = canonicalizeAssignee(name);
  if (!text) return null;
  const fixed = ASSIGNEE_COLORS[text.toLowerCase()];
  if (fixed) return fixed;
  let h = 0;
  for (let i = 0; i < text.length; i++) h = text.charCodeAt(i) + ((h << 5) - h);
  return `hsl(${ASSIGNEE_HUES[Math.abs(h) % ASSIGNEE_HUES.length]}, 62%, 58%)`;
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
    const a = canonicalizeAssignee(t.assignee);
    if (a) names.add(a);
  }
  return [...names].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

export function taskBarColor(task, statusColors, status) {
  const assignee = canonicalizeAssignee(task.assignee);
  if (assignee) return assigneeColor(assignee);
  return statusColors[status] || statusColors["Not started"];
}
