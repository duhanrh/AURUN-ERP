"""Endpoints de Ventas (``/sales``): OV, KPIs y transiciones de estado (sección 7.3).

Lectura: ``sales:access``. Alta y cambios de estado: ``sales:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.presentation.router import build_accounting_service
from aurum.modules.audit.domain.actions import (
    SALES_ORDER_DELETE,
    SALES_ORDER_RESTORE,
    SALES_ORDER_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
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
    UpdateSalesOrderRequest,
    UpdateSalesStatusRequest,
)
from aurum.modules.terceros.infrastructure.repositories import SqlAlchemyPartyRepository
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/sales", tags=["sales"])

_read = Depends(require_permission("sales:access"))
_write = Depends(require_permission("sales:manage"))
_write_dep = require_permission("sales:manage")


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
        accounting=build_accounting_service(session, tenant_id),
    )


@router.get("/orders", response_model=list[SalesOrderResponse], dependencies=[_read])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[SalesOrderResponse]:
    views = await _service(session, tenant_id).list_orders(include_deleted=include_deleted)
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


@router.patch("/orders/{order_id}", response_model=SalesOrderResponse, dependencies=[_write])
async def update_order(
    order_id: uuid.UUID,
    payload: UpdateSalesOrderRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> SalesOrderResponse:
    view = await _service(session, tenant_id).update_order(order_id, payload.to_patch())
    await record_event(
        session, tenant_id, action=SALES_ORDER_UPDATE, entity_type="sales_order",
        entity_id=order_id, principal=principal, request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return SalesOrderResponse.from_view(view)


@router.delete("/orders/{order_id}", response_model=SalesOrderResponse, dependencies=[_write])
async def delete_order(
    order_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> SalesOrderResponse:
    view = await _service(session, tenant_id).delete_order(order_id)
    await record_event(
        session, tenant_id, action=SALES_ORDER_DELETE, entity_type="sales_order",
        entity_id=order_id, principal=principal, request=request,
        changes={"order_code": view.order_code},
    )
    return SalesOrderResponse.from_view(view)


@router.post("/orders/{order_id}/restore", response_model=SalesOrderResponse, dependencies=[_write])
async def restore_order(
    order_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> SalesOrderResponse:
    view = await _service(session, tenant_id).restore_order(order_id)
    await record_event(
        session, tenant_id, action=SALES_ORDER_RESTORE, entity_type="sales_order",
        entity_id=order_id, principal=principal, request=request,
    )
    return SalesOrderResponse.from_view(view)
