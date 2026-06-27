"""Router raíz de la API versionada (``/api/v1``).

Cada módulo de negocio (sección 7 del documento maestro) registrará aquí su
``APIRouter`` a medida que se implemente en las fases siguientes.
"""

from __future__ import annotations

from fastapi import APIRouter

from aurum.modules.auth.presentation.router import router as auth_router
from aurum.modules.tenants.presentation.router import router as platform_router
from aurum.modules.terceros.presentation.router import customers_router, suppliers_router
from aurum.modules.users.presentation.router import roles_router
from aurum.modules.users.presentation.router import router as users_router


def build_api_router(prefix: str) -> APIRouter:
    """Construye el router raíz versionado con todos los módulos montados."""
    api_router = APIRouter(prefix=prefix)

    api_router.include_router(auth_router)
    api_router.include_router(users_router)
    api_router.include_router(roles_router)
    api_router.include_router(customers_router)
    api_router.include_router(suppliers_router)
    api_router.include_router(platform_router)

    return api_router
