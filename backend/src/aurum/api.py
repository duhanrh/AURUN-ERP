"""Router raíz de la API versionada (``/api/v1``).

Cada módulo de negocio (sección 7 del documento maestro) registrará aquí su
``APIRouter`` a medida que se implemente en las fases siguientes.
"""

from __future__ import annotations

from fastapi import APIRouter


def build_api_router(prefix: str) -> APIRouter:
    """Construye el router raíz versionado con todos los módulos montados."""
    api_router = APIRouter(prefix=prefix)

    # Los routers de cada módulo se incluirán aquí. Ejemplo (Fase 2+):
    # from aurum.modules.auth.presentation.router import router as auth_router
    # api_router.include_router(auth_router)

    return api_router
