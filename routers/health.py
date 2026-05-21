from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter(tags=["health"])

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DIST_INDEX = STATIC_DIR / "dist" / "index.html"


@router.get("/health")
@router.head("/health")
def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "frontend_built": DIST_INDEX.is_file(),
        },
    )


@router.get("/")
def root():
    if not DIST_INDEX.is_file():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built. Run: cd frontend && npm ci && npm run build",
        )
    return RedirectResponse(url="/static/dist/index.html")
