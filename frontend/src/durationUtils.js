/** Mirrors duration.py — 1 work day = 7.5 hours. */

export const HOURS_PER_WORK_DAY = 7.5;

export function daysToWorkHours(days) {
  return (Number(days) || 0) * HOURS_PER_WORK_DAY;
}

export function formatWorkHours(hours) {
  if (hours % 1 === 0) return `${hours} h`;
  return `${hours.toFixed(1)} h`;
}
