from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from dependencies import get_project_id
from schemas import (
    DelayRequest,
    LogRequest,
    ProjectStartUpdate,
    ShiftRequest,
    TaskCreate,
    TaskReorder,
    TaskUpdate,
)
from services import export_service, project_service, task_service, training_service

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/export")
def export_tasks_csv(project_id: str = Depends(get_project_id)):
    csv_text = export_service.tasks_to_csv(project_id)
    filename = f"{project_id}-tasks-{date.today().isoformat()}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tasks")
def get_tasks(project_id: str = Depends(get_project_id)):
    return project_service.get_tasks_payload(project_id)


@router.get("/modules")
def get_modules(project_id: str = Depends(get_project_id)):
    return training_service.get_modules_payload(project_id)


@router.get("/modules/tasks")
def get_module_tasks(
    project_id: str = Depends(get_project_id),
    module_index: Optional[int] = None,
    department: Optional[str] = None,
    subject: Optional[str] = None,
):
    return training_service.get_module_tasks_payload(
        project_id,
        module_index=module_index,
        department=department,
        subject=subject,
    )


@router.post("/tasks")
def create_task(
    body: TaskCreate,
    project_id: str = Depends(get_project_id),
):
    return task_service.create_task(project_id, body)


@router.put("/project-start")
def update_project_start(
    update: ProjectStartUpdate,
    project_id: str = Depends(get_project_id),
):
    return project_service.update_project_start(project_id, update.project_start)


@router.put("/tasks/reorder")
def reorder_tasks(
    body: TaskReorder,
    project_id: str = Depends(get_project_id),
):
    return task_service.reorder_tasks(project_id, body)


@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    update: TaskUpdate,
    project_id: str = Depends(get_project_id),
):
    return task_service.update_task(project_id, task_id, update)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    project_id: str = Depends(get_project_id),
):
    return task_service.delete_task(project_id, task_id)


@router.post("/shift")
def shift_timeline(
    request: ShiftRequest,
    project_id: str = Depends(get_project_id),
):
    return project_service.shift_timeline(project_id, request.extra_days)


@router.post("/tasks/{task_id}/log")
def append_task_log(
    task_id: int,
    body: LogRequest,
    project_id: str = Depends(get_project_id),
):
    return task_service.append_task_log(project_id, task_id, body)


@router.post("/tasks/{task_id}/delay")
def log_task_delay(
    task_id: int,
    body: DelayRequest,
    project_id: str = Depends(get_project_id),
):
    return task_service.log_task_delay(project_id, task_id, body)
