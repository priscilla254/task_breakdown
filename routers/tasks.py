from fastapi import APIRouter, Depends

from dependencies import get_project_id
from schemas import (
    DelayRequest,
    LogRequest,
    ProjectStartUpdate,
    ShiftRequest,
    TaskCreate,
    TaskUpdate,
)
from services import project_service, task_service

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/tasks")
def get_tasks(project_id: str = Depends(get_project_id)):
    return project_service.get_tasks_payload(project_id)


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
