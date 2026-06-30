"""Endpoints del Inventario (``/inventory``): materiales, lotes y KPIs (sección 7.1).

Lectura: ``inventory:access``. Escritura (alta de lote): ``inventory:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import (
    LOT_DELETE,
    LOT_RESTORE,
    LOT_UPDATE,
    MATERIAL_CREATE,
    MATERIAL_DELETE,
    MATERIAL_RESTORE,
    MATERIAL_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.inventory.presentation.schemas import (
    CreateLotRequest,
    CreateMaterialRequest,
    InventoryKpisResponse,
    LotResponse,
    MaterialResponse,
    UpdateLotRequest,
    UpdateMaterialRequest,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/inventory", tags=["inventory"])

_read = Depends(require_permission("inventory:access"))
_write = Depends(require_permission("inventory:manage"))
_write_dep = require_permission("inventory:manage")


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


@router.get("/materials/catalog", response_model=list[MaterialResponse], dependencies=[_read])
async def list_material_catalog(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[MaterialResponse]:
    views = await _service(session, tenant_id).list_catalog(include_deleted=include_deleted)
    return [MaterialResponse.from_view(v) for v in views]


@router.post(
    "/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_material(
    payload: CreateMaterialRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> MaterialResponse:
    view = await _service(session, tenant_id).create_material(payload.to_dto())
    await record_event(
        session,
        tenant_id,
        action=MATERIAL_CREATE,
        entity_type="material",
        entity_id=view.id,
        principal=principal,
        request=request,
        changes={"code": view.code, "name": view.name},
    )
    return MaterialResponse.from_view(view)


@router.patch("/materials/{material_id}", response_model=MaterialResponse, dependencies=[_write])
async def update_material(
    material_id: uuid.UUID,
    payload: UpdateMaterialRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> MaterialResponse:
    view = await _service(session, tenant_id).update_material(material_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=MATERIAL_UPDATE,
        entity_type="material",
        entity_id=material_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True),
    )
    return MaterialResponse.from_view(view)


@router.delete("/materials/{material_id}", response_model=MaterialResponse, dependencies=[_write])
async def delete_material(
    material_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> MaterialResponse:
    view = await _service(session, tenant_id).delete_material(material_id)
    await record_event(
        session,
        tenant_id,
        action=MATERIAL_DELETE,
        entity_type="material",
        entity_id=material_id,
        principal=principal,
        request=request,
        changes={"code": view.code},
    )
    return MaterialResponse.from_view(view)


@router.post(
    "/materials/{material_id}/restore", response_model=MaterialResponse, dependencies=[_write]
)
async def restore_material(
    material_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> MaterialResponse:
    view = await _service(session, tenant_id).restore_material(material_id)
    await record_event(
        session,
        tenant_id,
        action=MATERIAL_RESTORE,
        entity_type="material",
        entity_id=material_id,
        principal=principal,
        request=request,
    )
    return MaterialResponse.from_view(view)


@router.get("/lots", response_model=list[LotResponse], dependencies=[_read])
async def list_lots(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[LotResponse]:
    views = await _service(session, tenant_id).list_lots(include_deleted=include_deleted)
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


@router.patch("/lots/{lot_id}", response_model=LotResponse, dependencies=[_write])
async def update_lot(
    lot_id: uuid.UUID,
    payload: UpdateLotRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> LotResponse:
    view = await _service(session, tenant_id).update_lot(lot_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=LOT_UPDATE,
        entity_type="inventory_lot",
        entity_id=lot_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return LotResponse.from_view(view)


@router.delete("/lots/{lot_id}", response_model=LotResponse, dependencies=[_write])
async def delete_lot(
    lot_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> LotResponse:
    view = await _service(session, tenant_id).delete_lot(lot_id)
    await record_event(
        session,
        tenant_id,
        action=LOT_DELETE,
        entity_type="inventory_lot",
        entity_id=lot_id,
        principal=principal,
        request=request,
        changes={"lot_code": view.lot_code},
    )
    return LotResponse.from_view(view)


@router.post("/lots/{lot_id}/restore", response_model=LotResponse, dependencies=[_write])
async def restore_lot(
    lot_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> LotResponse:
    view = await _service(session, tenant_id).undelete_lot(lot_id)
    await record_event(
        session,
        tenant_id,
        action=LOT_RESTORE,
        entity_type="inventory_lot",
        entity_id=lot_id,
        principal=principal,
        request=request,
    )
    return LotResponse.from_view(view)
