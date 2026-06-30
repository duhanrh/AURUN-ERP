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
    CONFIG_COMPANY_UPDATE,
    CONFIG_MODULE_TOGGLE,
    CONFIG_PARAMETERS_UPDATE,
    CURRENCY_CREATE,
    CURRENCY_DELETE,
    CURRENCY_RESTORE,
    CURRENCY_SET_BASE,
    CURRENCY_UPDATE,
    UNIT_CREATE,
    UNIT_DELETE,
    UNIT_RESTORE,
    UNIT_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import (
    Principal,
    get_current_principal,
    require_permission,
)
from aurum.modules.config.application.currency_service import CurrencyService
from aurum.modules.config.application.services import ConfigService
from aurum.modules.config.application.units_service import UnitOfMeasureService
from aurum.modules.config.infrastructure.repositories import (
    SqlAlchemyBrandingRepository,
    SqlAlchemyCompanyRepository,
    SqlAlchemyCurrencyRepository,
    SqlAlchemyModuleConfigRepository,
    SqlAlchemyParametersRepository,
    SqlAlchemyUnitOfMeasureRepository,
)
from aurum.modules.config.presentation.schemas import (
    BrandingResponse,
    CompanyResponse,
    ConvertRequest,
    ConvertResponse,
    CreateCurrencyRequest,
    CreateUnitRequest,
    CurrencyResponse,
    ModuleResponse,
    ParametersResponse,
    SetModuleRequest,
    UnitResponse,
    UpdateBrandingRequest,
    UpdateCompanyRequest,
    UpdateCurrencyRequest,
    UpdateParametersRequest,
    UpdateUnitRequest,
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
        company=SqlAlchemyCompanyRepository(session),
    )


def _units(session: AsyncSession, tenant_id: uuid.UUID) -> UnitOfMeasureService:
    return UnitOfMeasureService(
        tenant_id=tenant_id, units=SqlAlchemyUnitOfMeasureRepository(session)
    )


def _currencies(session: AsyncSession, tenant_id: uuid.UUID) -> CurrencyService:
    return CurrencyService(
        tenant_id=tenant_id,
        currencies=SqlAlchemyCurrencyRepository(session),
        parameters=SqlAlchemyParametersRepository(session),
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
        session,
        tenant_id,
        action=CONFIG_BRANDING_UPDATE,
        entity_type="branding",
        principal=principal,
        request=request,
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
        session,
        tenant_id,
        action=CONFIG_BRANDING_RESET,
        entity_type="branding",
        principal=principal,
        request=request,
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
        session,
        tenant_id,
        action=CONFIG_PARAMETERS_UPDATE,
        entity_type="parameters",
        principal=principal,
        request=request,
        changes=payload.model_dump(mode="json"),
    )
    return ParametersResponse.from_view(view)


# ── Módulos ──────────────────────────────────────────────────────────────────
# Lectura con solo autenticación: el sidebar de cualquier usuario necesita saber qué
# módulos están activos para el tenant (no es información sensible). El alta/cambio
# (PUT) sí exige configuration:manage.
@router.get("/modules", response_model=list[ModuleResponse], dependencies=[_auth])
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
        session,
        tenant_id,
        action=CONFIG_MODULE_TOGGLE,
        entity_type="module",
        principal=principal,
        request=request,
        changes={"module_key": module_key, "is_active": payload.is_active},
    )
    return ModuleResponse.from_view(view)


# ── Unidades de medida ───────────────────────────────────────────────────────
@router.get("/units", response_model=list[UnitResponse], dependencies=[_read])
async def list_units(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = False,
) -> list[UnitResponse]:
    views = await _units(session, tenant_id).list_units(include_deleted=include_deleted)
    return [UnitResponse.from_view(v) for v in views]


@router.post("/units/convert", response_model=ConvertResponse, dependencies=[_read])
async def convert_units(
    payload: ConvertRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> ConvertResponse:
    res = await _units(session, tenant_id).convert(
        payload.quantity, payload.from_unit, payload.to_unit
    )
    return ConvertResponse(
        quantity=payload.quantity,
        from_unit=payload.from_unit,
        to_unit=payload.to_unit,
        grams=res.grams,
        result=res.result,
    )


@router.post("/units", response_model=UnitResponse)
async def create_unit(
    payload: CreateUnitRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> UnitResponse:
    view = await _units(session, tenant_id).create_unit(payload.to_dto())
    await record_event(
        session,
        tenant_id,
        action=UNIT_CREATE,
        entity_type="unit_of_measure",
        entity_id=uuid.UUID(view.id),
        principal=principal,
        request=request,
        changes={"code": view.code, "grams_factor": str(view.grams_factor)},
    )
    return UnitResponse.from_view(view)


@router.patch("/units/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: uuid.UUID,
    payload: UpdateUnitRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> UnitResponse:
    view = await _units(session, tenant_id).update_unit(unit_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=UNIT_UPDATE,
        entity_type="unit_of_measure",
        entity_id=unit_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return UnitResponse.from_view(view)


@router.delete("/units/{unit_id}", response_model=UnitResponse)
async def delete_unit(
    unit_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> UnitResponse:
    view = await _units(session, tenant_id).delete_unit(unit_id)
    await record_event(
        session,
        tenant_id,
        action=UNIT_DELETE,
        entity_type="unit_of_measure",
        entity_id=unit_id,
        principal=principal,
        request=request,
        changes={"code": view.code},
    )
    return UnitResponse.from_view(view)


@router.post("/units/{unit_id}/restore", response_model=UnitResponse)
async def restore_unit(
    unit_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> UnitResponse:
    view = await _units(session, tenant_id).restore_unit(unit_id)
    await record_event(
        session,
        tenant_id,
        action=UNIT_RESTORE,
        entity_type="unit_of_measure",
        entity_id=unit_id,
        principal=principal,
        request=request,
    )
    return UnitResponse.from_view(view)


# ── Datos del comercio / empresa ─────────────────────────────────────────────
@router.get("/company", response_model=CompanyResponse, dependencies=[_read])
async def get_company(session: AsyncSession = Depends(get_session)) -> CompanyResponse:
    return CompanyResponse.from_view(await _service(session).get_company())


@router.put("/company", response_model=CompanyResponse)
async def update_company(
    payload: UpdateCompanyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CompanyResponse:
    view = await _service(session).update_company(payload.to_dto())
    await record_event(
        session,
        tenant_id,
        action=CONFIG_COMPANY_UPDATE,
        entity_type="company",
        principal=principal,
        request=request,
        changes=payload.model_dump(mode="json"),
    )
    return CompanyResponse.from_view(view)


# ── Monedas ──────────────────────────────────────────────────────────────────
@router.get("/currencies", response_model=list[CurrencyResponse], dependencies=[_read])
async def list_currencies(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = False,
) -> list[CurrencyResponse]:
    views = await _currencies(session, tenant_id).list_currencies(include_deleted=include_deleted)
    return [CurrencyResponse.from_view(v) for v in views]


@router.post("/currencies", response_model=CurrencyResponse)
async def create_currency(
    payload: CreateCurrencyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CurrencyResponse:
    view = await _currencies(session, tenant_id).create_currency(payload.to_dto())
    await record_event(
        session,
        tenant_id,
        action=CURRENCY_CREATE,
        entity_type="currency",
        entity_id=uuid.UUID(view.id),
        principal=principal,
        request=request,
        changes={"code": view.code},
    )
    return CurrencyResponse.from_view(view)


@router.patch("/currencies/{currency_id}", response_model=CurrencyResponse)
async def update_currency(
    currency_id: uuid.UUID,
    payload: UpdateCurrencyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CurrencyResponse:
    view = await _currencies(session, tenant_id).update_currency(currency_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=CURRENCY_UPDATE,
        entity_type="currency",
        entity_id=currency_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return CurrencyResponse.from_view(view)


@router.post("/currencies/{currency_id}/set-base", response_model=CurrencyResponse)
async def set_base_currency(
    currency_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CurrencyResponse:
    view = await _currencies(session, tenant_id).set_base(currency_id)
    await record_event(
        session,
        tenant_id,
        action=CURRENCY_SET_BASE,
        entity_type="currency",
        entity_id=currency_id,
        principal=principal,
        request=request,
        changes={"code": view.code},
    )
    return CurrencyResponse.from_view(view)


@router.delete("/currencies/{currency_id}", response_model=CurrencyResponse)
async def delete_currency(
    currency_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CurrencyResponse:
    view = await _currencies(session, tenant_id).delete_currency(currency_id)
    await record_event(
        session,
        tenant_id,
        action=CURRENCY_DELETE,
        entity_type="currency",
        entity_id=currency_id,
        principal=principal,
        request=request,
        changes={"code": view.code},
    )
    return CurrencyResponse.from_view(view)


@router.post("/currencies/{currency_id}/restore", response_model=CurrencyResponse)
async def restore_currency(
    currency_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manage,
) -> CurrencyResponse:
    view = await _currencies(session, tenant_id).restore_currency(currency_id)
    await record_event(
        session,
        tenant_id,
        action=CURRENCY_RESTORE,
        entity_type="currency",
        entity_id=currency_id,
        principal=principal,
        request=request,
    )
    return CurrencyResponse.from_view(view)
