function formatTaskLine(t) {
  return `${t.id}: ${t.task}`;
}

export function confirmDeleteTask(task, allTasks) {
  const dependents = allTasks.filter(
    (t) => t.id !== task.id && (t.depends_on || []).includes(task.id)
  );
  const base = `Delete task ${formatTaskLine(task)}?\n\nThis cannot be undone.`;
  if (dependents.length === 0) {
    return window.confirm(`${base}\n\nThe timeline will recalculate.`);
  }
  const dependentLines = dependents.map((t) => `  • ${formatTaskLine(t)}`).join("\n");
  return window.confirm(
    `${base}\n\n${dependents.length} task(s) depend on this task:\n${dependentLines}\n\n` +
      `That link will be removed and dates will recalculate.`
  );
}
