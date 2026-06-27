"""Endpoints de Configuración (``/configuration``): marca, parámetros, módulos (7.17).

Lectura de marca: cualquier usuario autenticado (la necesita para aplicar el tema).
Lectura de parámetros/módulos: ``configuration:access``. Escrituras: ``configuration:manage``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.presentation.dependencies import (
    get_current_principal,
    require_permission,
)
from aurum.modules.config.application.services import ConfigService
from aurum.modules.config.infrastructure.repositories import (
    SqlAlchemyBrandingRepository,
    SqlAlchemyModuleConfigRepository,
    SqlAlchemyParametersRepository,
)
from aurum.modules.config.presentation.schemas import (
    BrandingResponse,
    ModuleResponse,
    ParametersResponse,
    SetModuleRequest,
    UpdateBrandingRequest,
    UpdateParametersRequest,
)
from aurum.shared.dependencies import get_session

router = APIRouter(prefix="/configuration", tags=["configuration"])

_auth = Depends(get_current_principal)
_read = Depends(require_permission("configuration:access"))
_write = Depends(require_permission("configuration:manage"))


def _service(session: AsyncSession) -> ConfigService:
    return ConfigService(
        branding=SqlAlchemyBrandingRepository(session),
        parameters=SqlAlchemyParametersRepository(session),
        modules=SqlAlchemyModuleConfigRepository(session),
    )


# ── Marca ────────────────────────────────────────────────────────────────────
@router.get("/branding", response_model=BrandingResponse, dependencies=[_auth])
async def get_branding(session: AsyncSession = Depends(get_session)) -> BrandingResponse:
    return BrandingResponse.from_view(await _service(session).get_branding())


@router.put("/branding", response_model=BrandingResponse, dependencies=[_write])
async def update_branding(
    payload: UpdateBrandingRequest,
    session: AsyncSession = Depends(get_session),
) -> BrandingResponse:
    return BrandingResponse.from_view(
        await _service(session).update_branding(payload.to_dto())
    )


@router.delete("/branding", response_model=BrandingResponse, dependencies=[_write])
async def reset_branding(session: AsyncSession = Depends(get_session)) -> BrandingResponse:
    return BrandingResponse.from_view(await _service(session).reset_branding())


# ── Parámetros ───────────────────────────────────────────────────────────────
@router.get("/parameters", response_model=ParametersResponse, dependencies=[_read])
async def get_parameters(session: AsyncSession = Depends(get_session)) -> ParametersResponse:
    return ParametersResponse.from_view(await _service(session).get_parameters())


@router.put("/parameters", response_model=ParametersResponse, dependencies=[_write])
async def update_parameters(
    payload: UpdateParametersRequest,
    session: AsyncSession = Depends(get_session),
) -> ParametersResponse:
    return ParametersResponse.from_view(
        await _service(session).update_parameters(payload.to_dto())
    )


# ── Módulos ──────────────────────────────────────────────────────────────────
@router.get("/modules", response_model=list[ModuleResponse], dependencies=[_read])
async def list_modules(session: AsyncSession = Depends(get_session)) -> list[ModuleResponse]:
    views = await _service(session).list_modules()
    return [ModuleResponse.from_view(v) for v in views]


@router.put("/modules/{module_key}", response_model=ModuleResponse, dependencies=[_write])
async def set_module(
    module_key: str,
    payload: SetModuleRequest,
    session: AsyncSession = Depends(get_session),
) -> ModuleResponse:
    view = await _service(session).set_module(module_key, payload.is_active)
    return ModuleResponse.from_view(view)
