/** Hours still to complete (not marked Completed). Includes logged delays on open tasks. */

export function getRemainingHours(tasks) {
  return tasks.reduce((sum, t) => {
    if (t.status === "Completed") return sum;
    const base = Number(t.hours) || 0;
    const delay = Number(t.delay_hours) || 0;
    return sum + base + delay;
  }, 0);
}
