"""Endpoints de Calidad (``/quality``): muestras de laboratorio y KPIs (sección 7.5).

Lectura: ``quality:access``. Registrar muestras: ``quality:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import (
    SAMPLE_DELETE,
    SAMPLE_RESTORE,
    SAMPLE_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.quality.application.services import QualityService
from aurum.modules.quality.infrastructure.repositories import SqlAlchemyQualitySampleRepository
from aurum.modules.quality.presentation.schemas import (
    CreateSampleRequest,
    QualityKpisResponse,
    QualitySampleResponse,
    UpdateSampleRequest,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/quality", tags=["quality"])

_read = Depends(require_permission("quality:access"))
_write = Depends(require_permission("quality:manage"))
_write_dep = require_permission("quality:manage")


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> QualityService:
    inventory = InventoryService(
        tenant_id=tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
    )
    return QualityService(
        tenant_id=tenant_id,
        samples=SqlAlchemyQualitySampleRepository(session),
        inventory=inventory,
    )


@router.get("/samples", response_model=list[QualitySampleResponse], dependencies=[_read])
async def list_samples(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[QualitySampleResponse]:
    views = await _service(session, tenant_id).list_samples(include_deleted=include_deleted)
    return [QualitySampleResponse.from_view(v) for v in views]


@router.get("/kpis", response_model=QualityKpisResponse, dependencies=[_read])
async def quality_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> QualityKpisResponse:
    return QualityKpisResponse.from_view(await _service(session, tenant_id).kpis())


@router.get("/samples/{sample_id}", response_model=QualitySampleResponse, dependencies=[_read])
async def get_sample(
    sample_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> QualitySampleResponse:
    return QualitySampleResponse.from_view(await _service(session, tenant_id).get_sample(sample_id))


@router.post(
    "/samples",
    response_model=QualitySampleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_write],
)
async def create_sample(
    payload: CreateSampleRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> QualitySampleResponse:
    view = await _service(session, tenant_id).create_sample(payload.to_new_sample())
    return QualitySampleResponse.from_view(view)


@router.patch("/samples/{sample_id}", response_model=QualitySampleResponse, dependencies=[_write])
async def update_sample(
    sample_id: uuid.UUID,
    payload: UpdateSampleRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> QualitySampleResponse:
    view = await _service(session, tenant_id).update_sample(sample_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=SAMPLE_UPDATE,
        entity_type="quality_sample",
        entity_id=sample_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return QualitySampleResponse.from_view(view)


@router.delete("/samples/{sample_id}", response_model=QualitySampleResponse, dependencies=[_write])
async def delete_sample(
    sample_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> QualitySampleResponse:
    view = await _service(session, tenant_id).delete_sample(sample_id)
    await record_event(
        session,
        tenant_id,
        action=SAMPLE_DELETE,
        entity_type="quality_sample",
        entity_id=sample_id,
        principal=principal,
        request=request,
        changes={"sample_code": view.sample_code},
    )
    return QualitySampleResponse.from_view(view)


@router.post(
    "/samples/{sample_id}/restore", response_model=QualitySampleResponse, dependencies=[_write]
)
async def restore_sample(
    sample_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_write_dep),
) -> QualitySampleResponse:
    view = await _service(session, tenant_id).restore_sample(sample_id)
    await record_event(
        session,
        tenant_id,
        action=SAMPLE_RESTORE,
        entity_type="quality_sample",
        entity_id=sample_id,
        principal=principal,
        request=request,
    )
    return QualitySampleResponse.from_view(view)
