const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "Not started", label: "Not started" },
  { value: "In progress", label: "In progress" },
  { value: "Completed", label: "Completed" },
];

export default function StatusFilterBar({
  filters,
  setFilter,
  clearFilters,
  anyActive,
  filteredCount,
  totalCount,
}) {
  return (
    <>
      <div className="training-filters task-filters" role="group" aria-label="Task filters">
        <label>
          Status
          <select value={filters.status} onChange={(e) => setFilter("status", e.target.value)}>
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        {anyActive ? (
          <button type="button" className="btn btn-ghost btn-filter-clear" onClick={clearFilters}>
            Clear filter
          </button>
        ) : null}
      </div>
      <p className="training-filter-summary">
        Showing <strong>{filteredCount}</strong> of <strong>{totalCount}</strong> tasks
        {anyActive ? (
          <span className="filter-summary-hint">
            {" "}
            — bar colour shows assignee; use this filter to focus by status
          </span>
        ) : null}
      </p>
    </>
  );
}
