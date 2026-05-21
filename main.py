"""
Application entry point: create FastAPI app, register routers, mount static files.

Layering:
  routers/     → HTTP (paths, status codes, Depends)
  services/    → business rules (create task, log delay, …)
  data_manager → persistence (JSON files)
  utils        → scheduling algorithm
  schemas      → Pydantic request bodies
  dependencies → shared FastAPI Depends (e.g. ?project=)
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from exceptions import AppError, BadRequestError, NotFoundError
from routers import health, projects, tasks

app = FastAPI(title="Tasks Gantt", version="1.0.0")

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(BadRequestError)
async def bad_request_handler(_request: Request, exc: BadRequestError):
    return JSONResponse(status_code=400, content={"detail": exc.message})


STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
