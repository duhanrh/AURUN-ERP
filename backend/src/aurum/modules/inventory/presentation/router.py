"""Endpoints del Inventario (``/inventory``): materiales, lotes y KPIs (sección 7.1).

Lectura: ``inventory:access``. Escritura (alta de lote): ``inventory:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.inventory.presentation.schemas import (
    CreateLotRequest,
    InventoryKpisResponse,
    LotResponse,
    MaterialResponse,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/inventory", tags=["inventory"])

_read = Depends(require_permission("inventory:access"))
_write = Depends(require_permission("inventory:manage"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> InventoryService:
    return InventoryService(
        tenant_id=tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
    )


@router.get("/materials", response_model=list[MaterialResponse], dependencies=[_read])
async def list_materials(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[MaterialResponse]:
    views = await _service(session, tenant_id).list_materials()
    return [MaterialResponse.from_view(v) for v in views]


@router.get("/lots", response_model=list[LotResponse], dependencies=[_read])
async def list_lots(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[LotResponse]:
    views = await _service(session, tenant_id).list_lots()
    return [LotResponse.from_view(v) for v in views]


@router.get("/kpis", response_model=InventoryKpisResponse, dependencies=[_read])
async def inventory_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> InventoryKpisResponse:
    return InventoryKpisResponse.from_view(await _service(session, tenant_id).kpis())


@router.get("/lots/{lot_id}", response_model=LotResponse, dependencies=[_read])
async def get_lot(
    lot_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> LotResponse:
    return LotResponse.from_view(await _service(session, tenant_id).get_lot(lot_id))


@router.post(
    "/lots",
    response_model=LotResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_lot(
    payload: CreateLotRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> LotResponse:
    view = await _service(session, tenant_id).create_lot(payload.to_new_lot())
    return LotResponse.from_view(view)
