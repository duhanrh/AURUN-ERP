"""Endpoints de Ventas (``/sales``): OV, KPIs y transiciones de estado (sección 7.3).

Lectura: ``sales:access``. Alta y cambios de estado: ``sales:manage``.
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
from aurum.modules.sales.application.services import SalesService
from aurum.modules.sales.infrastructure.repositories import SqlAlchemySalesOrderRepository
from aurum.modules.sales.presentation.schemas import (
    CreateSalesOrderRequest,
    SalesKpisResponse,
    SalesOrderResponse,
    UpdateSalesStatusRequest,
)
from aurum.modules.terceros.infrastructure.repositories import SqlAlchemyPartyRepository
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/sales", tags=["sales"])

_read = Depends(require_permission("sales:access"))
_write = Depends(require_permission("sales:manage"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> SalesService:
    inventory = InventoryService(
        tenant_id=tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
    )
    return SalesService(
        tenant_id=tenant_id,
        orders=SqlAlchemySalesOrderRepository(session),
        inventory=inventory,
        customers=SqlAlchemyPartyRepository(session),
    )


@router.get("/orders", response_model=list[SalesOrderResponse], dependencies=[_read])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[SalesOrderResponse]:
    views = await _service(session, tenant_id).list_orders()
    return [SalesOrderResponse.from_view(v) for v in views]


@router.get("/kpis", response_model=SalesKpisResponse, dependencies=[_read])
async def sales_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> SalesKpisResponse:
    return SalesKpisResponse.from_view(await _service(session, tenant_id).kpis())


@router.get("/orders/{order_id}", response_model=SalesOrderResponse, dependencies=[_read])
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> SalesOrderResponse:
    return SalesOrderResponse.from_view(await _service(session, tenant_id).get_order(order_id))


@router.post(
    "/orders",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_order(
    payload: CreateSalesOrderRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> SalesOrderResponse:
    view = await _service(session, tenant_id).create_order(payload.to_new_order())
    return SalesOrderResponse.from_view(view)


@router.patch("/orders/{order_id}/status", response_model=SalesOrderResponse, dependencies=[_write])
async def update_status(
    order_id: uuid.UUID,
    payload: UpdateSalesStatusRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> SalesOrderResponse:
    view = await _service(session, tenant_id).set_status(order_id, payload.status)
    return SalesOrderResponse.from_view(view)
