"""Endpoints de salud del sistema (liveness/readiness)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from aurum import __version__

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str = "aurum-erp-backend"


@router.get("/health", summary="Liveness probe")
async def health() -> HealthResponse:
    """Indica que el proceso está vivo y respondiendo."""
    return HealthResponse(status="ok", version=__version__)
