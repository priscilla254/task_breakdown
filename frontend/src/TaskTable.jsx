import { useMemo } from "react";
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
import { sortProjectTasks } from "./taskSort";
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
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: t.id, disabled: !reorderEnabled });

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
      className={`task-row-clickable${isDragging ? " training-row-dragging" : ""}`}
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
          step="1"
          min="1"
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

export default function TaskTable({
  tasks,
  onUpdate,
  onReorder,
  onTaskSelect,
  onEditSchedule,
  onDelete,
  reorderEnabled = true,
}) {
  const orderedTasks = useMemo(() => sortProjectTasks(tasks), [tasks]);
  const taskIds = useMemo(() => orderedTasks.map((t) => t.id), [orderedTasks]);

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

    const oldIndex = taskIds.indexOf(active.id);
    const newIndex = taskIds.indexOf(over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    onReorder(arrayMove(taskIds, oldIndex, newIndex));
  };

  return (
    <div className="table-scroll">
      {reorderEnabled ? (
        <p className="table-reorder-hint">
          Drag rows to change display order. Start/end: pick dates to override auto-schedule (highlighted
          border = manual). Clear a date to revert to auto.
        </p>
      ) : (
        <p className="table-reorder-hint table-reorder-hint-muted">
          Clear the status filter to drag and reorder rows.
        </p>
      )}
      <table>
        <thead>
          <tr>
            {reorderEnabled ? <th className="drag-handle-col" aria-label="Reorder" /> : null}
            <th>Task</th>
            <th>Assignee</th>
            <th>Deps</th>
            <th>Start</th>
            <th>End</th>
            <th>Days</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={taskIds} strategy={verticalListSortingStrategy} disabled={!reorderEnabled}>
            <tbody>
              {orderedTasks.map((t) => (
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
            </tbody>
          </SortableContext>
        </DndContext>
      </table>
    </div>
  );
}
