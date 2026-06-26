"""Punto de entrada de la aplicación FastAPI (app factory).

Ensambla configuración, logging, middleware (CORS, request id, resolución de
tenant), manejo global de errores, router de salud y el router raíz versionado
``/api/v1``. La lógica de negocio vive en ``aurum.modules.*``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aurum import __version__
from aurum.api import build_api_router
from aurum.shared.config import Settings, get_settings
from aurum.shared.errors import register_exception_handlers
from aurum.shared.health import router as health_router
from aurum.shared.infrastructure.database import dispose_engine
from aurum.shared.logging import configure_logging
from aurum.shared.middleware import RequestContextMiddleware, TenantResolutionMiddleware


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida: libera recursos (engine de BD) al apagar."""
    yield
    await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea y configura la instancia de FastAPI."""
    settings = settings or get_settings()
    configure_logging(logging.DEBUG if settings.debug else logging.INFO)

    app = FastAPI(
        title="AURUM ERP API",
        version=__version__,
        description="API multi-tenant para gestión de minería de metales preciosos.",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.debug,
        lifespan=_lifespan,
    )

    # Middleware. El último añadido es el más externo (se ejecuta primero):
    # RequestContext (request_id) envuelve a la resolución de tenant.
    app.add_middleware(TenantResolutionMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Salud en la raíz (no versionada) + API de negocio versionada.
    app.include_router(health_router)
    app.include_router(build_api_router(settings.api_prefix))

    return app


app = create_app()
