"""Endpoints de Transformación (``/transformation``): OT y pipeline (sección 7.4).

Lectura: ``transformation:access``. Alta y transiciones (avanzar/completar/cancelar):
``transformation:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import (
    TRANSFORMATION_DELETE,
    TRANSFORMATION_RESTORE,
    TRANSFORMATION_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.transformation.application.services import TransformationService
from aurum.modules.transformation.infrastructure.repositories import (
    SqlAlchemyTransformationOrderRepository,
)
from aurum.modules.transformation.presentation.schemas import (
    CreateTransformationOrderRequest,
    TransformationKpisResponse,
    TransformationOrderResponse,
    UpdateTransformationOrderRequest,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/transformation", tags=["transformation"])

_read = Depends(require_permission("transformation:access"))
_write = Depends(require_permission("transformation:manage"))
_write_dep = require_permission("transformation:manage")


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> TransformationService:
    materials = SqlAlchemyMaterialRepository(session)
    inventory = InventoryService(
        tenant_id=tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=materials,
    )
    return TransformationService(
        tenant_id=tenant_id,
        orders=SqlAlchemyTransformationOrderRepository(session),
        inventory=inventory,
        materials=materials,
    )


@router.get("/orders", response_model=list[TransformationOrderResponse], dependencies=[_read])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[TransformationOrderResponse]:
    views = await _service(session, tenant_id).list_orders(include_deleted=include_deleted)
    return [TransformationOrderResponse.from_view(v) for v in views]


@router.patch(
    "/orders/{order_id}", response_model=TransformationOrderResponse, dependencies=[_write]
)
async def update_order(
    order_id: uuid.UUID,
    payload: UpdateTransformationOrderRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).update_order(order_id, payload.to_patch())
    await record_event(
        session, tenant_id, action=TRANSFORMATION_UPDATE, entity_type="transformation_order",
        entity_id=order_id, principal=principal, request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return TransformationOrderResponse.from_view(view)


@router.delete(
    "/orders/{order_id}", response_model=TransformationOrderResponse, dependencies=[_write]
)
async def delete_order(
    order_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).delete_order(order_id)
    await record_event(
        session, tenant_id, action=TRANSFORMATION_DELETE, entity_type="transformation_order",
        entity_id=order_id, principal=principal, request=request,
        changes={"order_code": view.order_code},
    )
    return TransformationOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/restore",
    response_model=TransformationOrderResponse,
    dependencies=[_write],
)
async def restore_order(
    order_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).restore_order(order_id)
    await record_event(
        session, tenant_id, action=TRANSFORMATION_RESTORE, entity_type="transformation_order",
        entity_id=order_id, principal=principal, request=request,
    )
    return TransformationOrderResponse.from_view(view)


@router.get("/kpis", response_model=TransformationKpisResponse, dependencies=[_read])
async def transformation_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationKpisResponse:
    return TransformationKpisResponse.from_view(await _service(session, tenant_id).kpis())


@router.get(
    "/orders/{order_id}", response_model=TransformationOrderResponse, dependencies=[_read]
)
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).get_order(order_id)
    return TransformationOrderResponse.from_view(view)


@router.post(
    "/orders",
    response_model=TransformationOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_order(
    payload: CreateTransformationOrderRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).create_order(payload.to_new_order())
    return TransformationOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/advance",
    response_model=TransformationOrderResponse,
    dependencies=[_write],
)
async def advance_stage(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).advance_stage(order_id)
    return TransformationOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/complete",
    response_model=TransformationOrderResponse,
    dependencies=[_write],
)
async def complete_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).complete_order(order_id)
    return TransformationOrderResponse.from_view(view)


@router.post(
    "/orders/{order_id}/cancel",
    response_model=TransformationOrderResponse,
    dependencies=[_write],
)
async def cancel_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TransformationOrderResponse:
    view = await _service(session, tenant_id).cancel_order(order_id)
    return TransformationOrderResponse.from_view(view)
