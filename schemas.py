"""Pydantic models for API request/response bodies (HTTP contract)."""

from typing import List, Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    task: str
    hours: float = 8
    depends_on: List[int] = []
    status: str = "Not started"


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    hours: Optional[float] = None
    status: Optional[str] = None
    log: Optional[str] = None
    depends_on: Optional[List[int]] = None
    fixed_start: Optional[str] = None


class ProjectStartUpdate(BaseModel):
    project_start: str


class ShiftRequest(BaseModel):
    extra_days: int = 7


class LogRequest(BaseModel):
    message: str


class DelayRequest(BaseModel):
    hours: float
    reason: str
