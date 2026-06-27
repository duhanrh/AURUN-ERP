"""Endpoints de Compras (``/purchasing``): OC, KPIs y aprobación (sección 7.2).

Lectura: ``purchasing:access``. Alta: ``purchasing:manage``. Aprobar/rechazar:
``purchase_order:approve`` (acción sensible separada del alta, sección 10.2).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.presentation.router import build_accounting_service
from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.purchasing.application.services import PurchasingService
from aurum.modules.purchasing.infrastructure.repositories import (
    SqlAlchemyPurchaseOrderRepository,
)
from aurum.modules.purchasing.presentation.schemas import (
    CreatePurchaseOrderRequest,
    PurchaseOrderResponse,
    PurchasingKpisResponse,
)
from aurum.modules.terceros.infrastructure.repositories import SqlAlchemyPartyRepository
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/purchasing", tags=["purchasing"])

_read = Depends(require_permission("purchasing:access"))
_write = Depends(require_permission("purchasing:manage"))
_approve = Depends(require_permission("purchase_order:approve"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> PurchasingService:
    materials = SqlAlchemyMaterialRepository(session)
    inventory = InventoryService(
        tenant_id=tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=materials,
    )
    return PurchasingService(
        tenant_id=tenant_id,
        orders=SqlAlchemyPurchaseOrderRepository(session),
        inventory=inventory,
        materials=materials,
        suppliers=SqlAlchemyPartyRepository(session),
        accounting=build_accounting_service(session, tenant_id),
    )


@router.get("/orders", response_model=list[PurchaseOrderResponse], dependencies=[_read])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[PurchaseOrderResponse]:
    views = await _service(session, tenant_id).list_orders()
    return [PurchaseOrderResponse.from_view(v) for v in views]


@router.get("/kpis", response_model=PurchasingKpisResponse, dependencies=[_read])
async def purchasing_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> PurchasingKpisResponse:
    return PurchasingKpisResponse.from_view(await _service(session, tenant_id).kpis())


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse, dependencies=[_read])
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> PurchaseOrderResponse:
    return PurchaseOrderResponse.from_view(await _service(session, tenant_id).get_order(order_id))


@router.post(
    "/orders",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_order(
    payload: CreatePurchaseOrderRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> PurchaseOrderResponse:
    view = await _service(session, tenant_id).create_order(payload.to_new_order())
    return PurchaseOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/approve",
    response_model=PurchaseOrderResponse,
    dependencies=[_approve],
)
async def approve_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> PurchaseOrderResponse:
    view = await _service(session, tenant_id).approve_order(order_id)
    return PurchaseOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/reject",
    response_model=PurchaseOrderResponse,
    dependencies=[_approve],
)
async def reject_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> PurchaseOrderResponse:
    view = await _service(session, tenant_id).reject_order(order_id)
    return PurchaseOrderResponse.from_view(view)
