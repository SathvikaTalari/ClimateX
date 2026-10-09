from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    """
    Returns service health status and a database connectivity check.
    Always returns HTTP 200 if the service is up; 503 if DB is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": db_status,
        "version": "0.1.0",
    }
