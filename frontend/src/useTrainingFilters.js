import { useEffect, useMemo, useState } from "react";
import {
  EMPTY_TRAINING_FILTERS,
  filterTrainingTasks,
  getTrainingFilterOptions,
} from "./trainingUtils";

export function useTrainingFilters(tasks, enabled) {
  const [filters, setFilters] = useState(EMPTY_TRAINING_FILTERS);

  useEffect(() => {
    if (!enabled) setFilters(EMPTY_TRAINING_FILTERS);
  }, [enabled]);

  const options = useMemo(
    () => (enabled ? getTrainingFilterOptions(tasks) : { departments: [], subjects: [], assignees: [], subjectsByDepartment: {} }),
    [tasks, enabled]
  );

  const subjectChoices = useMemo(() => {
    if (!enabled) return [];
    if (filters.department !== "all") {
      return options.subjectsByDepartment[filters.department] || [];
    }
    return options.subjects;
  }, [enabled, filters.department, options]);

  useEffect(() => {
    if (!enabled) return;
    if (filters.subject !== "all" && !subjectChoices.includes(filters.subject)) {
      setFilters((f) => ({ ...f, subject: "all" }));
    }
  }, [enabled, filters.subject, subjectChoices]);

  const filteredTasks = useMemo(
    () => (enabled ? filterTrainingTasks(tasks, filters) : tasks),
    [tasks, filters, enabled]
  );

  const setFilter = (key, value) => {
    setFilters((prev) => {
      const next = { ...prev, [key]: value };
      if (key === "department") next.subject = "all";
      return next;
    });
  };

  const clearFilters = () => setFilters(EMPTY_TRAINING_FILTERS);

  const anyActive =
    enabled &&
    (filters.phase !== "all" ||
      filters.department !== "all" ||
      filters.subject !== "all" ||
      filters.assignee !== "all");

  return {
    filters,
    setFilter,
    clearFilters,
    options,
    subjectChoices,
    filteredTasks,
    anyActive,
    totalCount: tasks.length,
    filteredCount: filteredTasks.length,
  };
}
