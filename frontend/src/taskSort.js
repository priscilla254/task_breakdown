/** Display order for non-training projects (default: task id). */

function defaultCompare(a, b) {
  return a.id - b.id;
}

export function sortProjectTasks(tasks) {
  const hasCustomOrder = tasks.some((t) => t.display_order != null);
  if (!hasCustomOrder) {
    return [...tasks].sort(defaultCompare);
  }
  return [...tasks].sort((a, b) => {
    const oa = a.display_order ?? Number.MAX_SAFE_INTEGER;
    const ob = b.display_order ?? Number.MAX_SAFE_INTEGER;
    if (oa !== ob) return oa - ob;
    return defaultCompare(a, b);
  });
}
