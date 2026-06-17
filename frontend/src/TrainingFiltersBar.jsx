export default function TrainingFiltersBar({
  filters,
  setFilter,
  clearFilters,
  options,
  subjectChoices,
  anyActive,
  filteredCount,
  totalCount,
}) {
  return (
    <>
      <div className="training-filters" role="group" aria-label="Task filters">
        <label>
          Phase
          <select value={filters.phase} onChange={(e) => setFilter("phase", e.target.value)}>
            <option value="all">All</option>
            <option value="content">Content</option>
            <option value="development">Development</option>
            <option value="upload">Upload</option>
          </select>
        </label>
        <label>
          Department
          <select
            value={filters.department}
            onChange={(e) => setFilter("department", e.target.value)}
          >
            <option value="all">All</option>
            {options.departments.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label>
          Subject
          <select value={filters.subject} onChange={(e) => setFilter("subject", e.target.value)}>
            <option value="all">All</option>
            {subjectChoices.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Assignee
          <select
            value={filters.assignee}
            onChange={(e) => setFilter("assignee", e.target.value)}
          >
            <option value="all">All</option>
            <option value="unassigned">Unassigned</option>
            {options.assignees.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        {anyActive ? (
          <button type="button" className="btn btn-ghost btn-filter-clear" onClick={clearFilters}>
            Clear filters
          </button>
        ) : null}
      </div>
      <p className="training-filter-summary">
        Showing <strong>{filteredCount}</strong> of <strong>{totalCount}</strong> tasks
      </p>
    </>
  );
}
