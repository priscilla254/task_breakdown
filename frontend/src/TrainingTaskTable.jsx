import { Fragment, useMemo } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  buildTrainingSubjectSections,
  mergeSubjectReorder,
} from "./trainingUtils";
import {
  trainingRowAssigneeClass,
} from "./assigneeColors";
import { TaskScheduleDateCells } from "./TaskScheduleDateCells";

function statusClass(status) {
  if (status === "In progress") return "status-in-progress";
  if (status === "Completed") return "status-completed";
  return "status-not-started";
}

function SortableTaskRow({
  task: t,
  onUpdate,
  onTaskSelect,
  onEditSchedule,
  onDelete,
  handleDepsBlur,
  handleAssigneeBlur,
  reorderEnabled,
}) {
  const sortable = useSortable({ id: t.id, disabled: !reorderEnabled });
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = sortable;

  const style = reorderEnabled
    ? {
        transform: CSS.Transform.toString(transform),
        transition,
      }
    : undefined;

  return (
    <tr
      ref={reorderEnabled ? setNodeRef : undefined}
      style={style}
      className={`task-row-clickable training-task-row training-task-phase-${t.phase || "other"} ${trainingRowAssigneeClass(t.assignee)}${isDragging ? " training-row-dragging" : ""}`}
      onClick={() => onTaskSelect?.(t)}
    >
      {reorderEnabled ? (
        <td className="drag-handle-cell">
          <button
            type="button"
            className="drag-handle"
            title="Drag to reorder"
            aria-label="Drag to reorder"
            onClick={(e) => e.stopPropagation()}
            {...attributes}
            {...listeners}
          >
            ⠿
          </button>
        </td>
      ) : null}
      <td className="task-name">{t.task}</td>
      <td>
        <span className={`phase-badge phase-${t.phase || "other"}`}>
          {t.phase === "development"
            ? "Dev"
            : t.phase === "content"
              ? "Content"
              : t.phase === "upload"
                ? "Upload"
                : "—"}
        </span>
      </td>
      <td>
        <input
          type="text"
          className="assignee-input"
          defaultValue={t.assignee || ""}
          placeholder="Who"
          onClick={(e) => e.stopPropagation()}
          onBlur={(e) => handleAssigneeBlur(t.id, e.target.value)}
        />
      </td>
      <td>
        <input
          type="text"
          defaultValue={(t.depends_on || []).join(", ")}
          placeholder="1, 6"
          onClick={(e) => e.stopPropagation()}
          onBlur={(e) => handleDepsBlur(t.id, e.target.value)}
        />
      </td>
      <TaskScheduleDateCells task={t} onUpdate={onUpdate} />
      <td>
        <input
          type="number"
          step="0.5"
          min="0"
          defaultValue={t.days}
          onClick={(e) => e.stopPropagation()}
          onBlur={(e) => onUpdate(t.id, { days: parseInt(e.target.value, 10) || 1 })}
        />
      </td>
      <td>
        <select
          defaultValue={t.status}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => onUpdate(t.id, { status: e.target.value })}
          className={`status-badge ${statusClass(t.status)}`}
        >
          <option>Not started</option>
          <option>In progress</option>
          <option>Completed</option>
        </select>
      </td>
      <td className="table-actions-cell">
        <button
          type="button"
          className="btn-table-edit"
          title="Update task"
          onClick={(e) => {
            e.stopPropagation();
            onEditSchedule?.(t);
          }}
        >
          Update
        </button>
        <button
          type="button"
          className="btn-table-delete"
          title="Delete task"
          onClick={(e) => {
            e.stopPropagation();
            onDelete?.(t);
          }}
        >
          Delete
        </button>
      </td>
    </tr>
  );
}

export default function TrainingTaskTable({
  tasks,
  allTasks,
  onUpdate,
  onReorder,
  onTaskSelect,
  onEditSchedule,
  onDelete,
  reorderEnabled = false,
}) {
  const sections = useMemo(() => buildTrainingSubjectSections(tasks), [tasks]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDepsBlur = (id, value) => {
    const depends_on = value.trim()
      ? value.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n))
      : [];
    onUpdate(id, { depends_on });
  };

  const handleAssigneeBlur = (id, value) => {
    onUpdate(id, { assignee: value.trim() || "" });
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id || !onReorder) return;

    const section = sections.find(
      (s) => s.tasks.some((t) => t.id === active.id) && s.tasks.some((t) => t.id === over.id)
    );
    if (!section) return;

    const ids = section.tasks.map((t) => t.id);
    const oldIndex = ids.indexOf(active.id);
    const newIndex = ids.indexOf(over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    const newSubjectOrder = arrayMove(ids, oldIndex, newIndex);
    const globalOrder = mergeSubjectReorder(
      allTasks || tasks,
      section.departmentRaw,
      section.subjectRaw,
      newSubjectOrder
    );
    onReorder(globalOrder);
  };

  const colSpan = reorderEnabled ? 10 : 9;

  const tableBody = (
    <tbody>
      {(() => {
        let lastDept = null;
        return sections.map((section) => {
          const showDeptHeader = section.department !== lastDept;
          if (showDeptHeader) lastDept = section.department;
          return (
            <SortableContext
              key={section.key}
              items={section.tasks.map((t) => t.id)}
              strategy={verticalListSortingStrategy}
              disabled={!reorderEnabled}
            >
              {showDeptHeader ? (
                <tr className="section-row section-row-department">
                  <td colSpan={colSpan}>{section.department}</td>
                </tr>
              ) : null}
              <tr className="section-row section-row-subject">
                <td colSpan={colSpan}>{section.subject}</td>
              </tr>
              {section.groups.map((group) => (
                <Fragment key={`group-${group.key}`}>
                  <tr
                    key={`parent-${group.key}`}
                    className={`section-row section-row-parent-step section-row-phase-${group.phase}`}
                  >
                    <td colSpan={colSpan}>
                      <span className={`phase-badge phase-${group.phase}`}>{group.label}</span>
                      <span className="parent-step-days">{group.spanDays} calendar days</span>
                    </td>
                  </tr>
                  {group.children.map((t) => (
                    <SortableTaskRow
                      key={t.id}
                      task={t}
                      onUpdate={onUpdate}
                      onTaskSelect={onTaskSelect}
                      onEditSchedule={onEditSchedule}
                      onDelete={onDelete}
                      handleDepsBlur={handleDepsBlur}
                      handleAssigneeBlur={handleAssigneeBlur}
                      reorderEnabled={reorderEnabled}
                    />
                  ))}
                </Fragment>
              ))}
            </SortableContext>
          );
        });
      })()}
    </tbody>
  );

  return (
    <div className="table-scroll">
      {reorderEnabled ? (
        <p className="table-reorder-hint">
          Drag rows within a subject to change display order. Start/end: pick dates to override
          auto-schedule (highlighted = manual). Clear a date to revert.
        </p>
      ) : (
        <p className="table-reorder-hint table-reorder-hint-muted">
          Clear filters to drag and reorder rows.
        </p>
      )}
      <div className="training-color-legend" aria-label="Training task colours">
        <span className="training-legend-group">
          <span className="training-legend-label">Phase:</span>
          <span className="legend-item">
            <span className="legend-swatch legend-swatch-phase-content" />
            Content
          </span>
          <span className="legend-item">
            <span className="legend-swatch legend-swatch-phase-development" />
            Development
          </span>
          <span className="legend-item">
            <span className="legend-swatch legend-swatch-phase-upload" />
            Upload
          </span>
        </span>
        <span className="training-legend-group">
          <span className="training-legend-label">Assignee:</span>
          <span className="legend-item">
            <span className="legend-swatch legend-swatch-priscilla" />
            Priscilla
          </span>
          <span className="legend-item">
            <span className="legend-swatch legend-swatch-unassigned" />
            Unassigned / management
          </span>
        </span>
      </div>
      <table className="training-table">
        <thead>
          <tr>
            {reorderEnabled ? <th className="drag-handle-col" aria-label="Reorder" /> : null}
            <th>Task</th>
            <th>Phase</th>
            <th>Assignee</th>
            <th>Deps</th>
            <th>Start</th>
            <th>End</th>
            <th>Days</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        {reorderEnabled ? (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            {tableBody}
          </DndContext>
        ) : (
          tableBody
        )}
      </table>
    </div>
  );
}
