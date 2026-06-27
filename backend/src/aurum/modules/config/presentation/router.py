"""Endpoints de Configuración (``/configuration``): marca, parámetros, módulos (7.17).

Lectura de marca: cualquier usuario autenticado (la necesita para aplicar el tema).
Lectura de parámetros/módulos: ``configuration:access``. Escrituras: ``configuration:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import (
    CONFIG_BRANDING_RESET,
    CONFIG_BRANDING_UPDATE,
    CONFIG_MODULE_TOGGLE,
    CONFIG_PARAMETERS_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import (
    Principal,
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
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/configuration", tags=["configuration"])

_auth = Depends(get_current_principal)
_read = Depends(require_permission("configuration:access"))
_manage = Depends(require_permission("configuration:manage"))


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


@router.put("/branding", response_model=BrandingResponse)
async def update_branding(
    payload: UpdateBrandingRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> BrandingResponse:
    view = await _service(session).update_branding(payload.to_dto())
    await record_event(
        session, tenant_id, action=CONFIG_BRANDING_UPDATE, entity_type="branding",
        principal=principal, request=request,
        changes=payload.model_dump(exclude_none=True),
    )
    return BrandingResponse.from_view(view)


@router.delete("/branding", response_model=BrandingResponse)
async def reset_branding(
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> BrandingResponse:
    view = await _service(session).reset_branding()
    await record_event(
        session, tenant_id, action=CONFIG_BRANDING_RESET, entity_type="branding",
        principal=principal, request=request,
    )
    return BrandingResponse.from_view(view)


# ── Parámetros ───────────────────────────────────────────────────────────────
@router.get("/parameters", response_model=ParametersResponse, dependencies=[_read])
async def get_parameters(session: AsyncSession = Depends(get_session)) -> ParametersResponse:
    return ParametersResponse.from_view(await _service(session).get_parameters())


@router.put("/parameters", response_model=ParametersResponse)
async def update_parameters(
    payload: UpdateParametersRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> ParametersResponse:
    view = await _service(session).update_parameters(payload.to_dto())
    await record_event(
        session, tenant_id, action=CONFIG_PARAMETERS_UPDATE, entity_type="parameters",
        principal=principal, request=request, changes=payload.model_dump(mode="json"),
    )
    return ParametersResponse.from_view(view)


# ── Módulos ──────────────────────────────────────────────────────────────────
@router.get("/modules", response_model=list[ModuleResponse], dependencies=[_read])
async def list_modules(session: AsyncSession = Depends(get_session)) -> list[ModuleResponse]:
    views = await _service(session).list_modules()
    return [ModuleResponse.from_view(v) for v in views]


@router.put("/modules/{module_key}", response_model=ModuleResponse)
async def set_module(
    module_key: str,
    payload: SetModuleRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> ModuleResponse:
    view = await _service(session).set_module(module_key, payload.is_active)
    await record_event(
        session, tenant_id, action=CONFIG_MODULE_TOGGLE, entity_type="module",
        principal=principal, request=request,
        changes={"module_key": module_key, "is_active": payload.is_active},
    )
    return ModuleResponse.from_view(view)
