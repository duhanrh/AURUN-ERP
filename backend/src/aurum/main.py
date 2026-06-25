"""Punto de entrada de la aplicación FastAPI (app factory).

Ensambla configuración, middleware (CORS), router de salud y el router raíz
versionado ``/api/v1``. La lógica de negocio vive en ``aurum.modules.*``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aurum import __version__
from aurum.api import build_api_router
from aurum.shared.config import Settings, get_settings
from aurum.shared.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea y configura la instancia de FastAPI."""
    settings = settings or get_settings()

    app = FastAPI(
        title="AURUM ERP API",
        version=__version__,
        description="API multi-tenant para gestión de minería de metales preciosos.",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Salud en la raíz (no versionada) + API de negocio versionada.
    app.include_router(health_router)
    app.include_router(build_api_router(settings.api_prefix))

    return app


app = create_app()
