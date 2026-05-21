"""
FastAPI dependencies: shared request inputs and injection.

Routers use Depends(get_project_id) instead of repeating Query + validation.
"""

from fastapi import Depends, HTTPException, Query

from data_manager import DEFAULT_PROJECT_ID, UnknownProjectError, resolve_project_id


def get_project_id(
    project: str = Query(DEFAULT_PROJECT_ID, alias="project"),
) -> str:
    """Validate ?project= and return a resolved project id."""
    try:
        return resolve_project_id(project)
    except UnknownProjectError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
