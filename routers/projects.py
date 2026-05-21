from fastapi import APIRouter

from services import project_service

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects")
def get_projects():
    return project_service.get_projects_payload()
