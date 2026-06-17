/** Remaining work days (not marked Completed). Includes logged delays on open tasks. */

export function getRemainingDays(tasks) {
  return tasks.reduce((sum, t) => {
    if (t.status === "Completed") return sum;
    const base = Number(t.days) || 0;
    const delay = Number(t.delay_days) || 0;
    return sum + base + delay;
  }, 0);
}
