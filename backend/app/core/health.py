"""Health checks. Version-independent, so they live at `/health`, not under `/api/v2`."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionDep
from app.core.exceptions import ServiceUnavailableError

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("")
def health() -> HealthResponse:
    """Liveness: the process is up. Does not touch the database."""
    return HealthResponse()


@router.get("/ready")
def readiness(session: SessionDep) -> HealthResponse:
    """Readiness: the database is reachable (use this to check your .env DB settings)."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ServiceUnavailableError("Database is unreachable") from exc
    return HealthResponse()
