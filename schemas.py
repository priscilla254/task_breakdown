"""Pydantic models for API request/response bodies (HTTP contract)."""

from typing import List, Optional, Union

from pydantic import BaseModel


class TaskCreate(BaseModel):
    task: str
    days: Union[int, float] = 1
    depends_on: List[int] = []
    status: str = "Not started"
    department: Optional[str] = None
    subject: Optional[str] = None
    assignee: Optional[str] = None


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    days: Optional[Union[int, float]] = None
    status: Optional[str] = None
    log: Optional[str] = None
    depends_on: Optional[List[int]] = None
    fixed_start: Optional[str] = None
    fixed_end: Optional[str] = None
    department: Optional[str] = None
    subject: Optional[str] = None
    assignee: Optional[str] = None
    display_order: Optional[int] = None


class TaskReorder(BaseModel):
    order: List[int]


class ProjectStartUpdate(BaseModel):
    project_start: str


class ShiftRequest(BaseModel):
    extra_days: int = 7


class LogRequest(BaseModel):
    message: str


class DelayRequest(BaseModel):
    days: int
    reason: str
