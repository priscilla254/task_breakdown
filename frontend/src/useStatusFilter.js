import { useMemo, useState } from "react";

export const EMPTY_STATUS_FILTER = { status: "all" };

export function filterByStatus(tasks, filters) {
  if (!filters || filters.status === "all") return tasks;
  return tasks.filter((t) => t.status === filters.status);
}

export function useStatusFilter(tasks, enabled) {
  const [filters, setFilters] = useState(EMPTY_STATUS_FILTER);

  const filteredTasks = useMemo(
    () => (enabled ? filterByStatus(tasks, filters) : tasks),
    [tasks, filters, enabled]
  );

  const setFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => setFilters(EMPTY_STATUS_FILTER);

  const anyActive = enabled && filters.status !== "all";

  return {
    filters,
    setFilter,
    clearFilters,
    filteredTasks,
    anyActive,
    filteredCount: filteredTasks.length,
    totalCount: tasks.length,
  };
}
