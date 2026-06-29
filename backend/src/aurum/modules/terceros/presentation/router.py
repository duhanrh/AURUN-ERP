"""Endpoints de Terceros: Clientes (``/customers``) y Proveedores (``/suppliers``).

Ambos recursos comparten implementación (un ``PartyService`` por ``kind``). La
lectura exige ``<kind>:access`` y la escritura ``<kind>:manage`` (RBAC de servidor,
sección 10.2). No hay borrado físico: dar de baja = ``PATCH status=inactive``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import PARTY_DELETE, PARTY_RESTORE
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.modules.terceros.application.services import PartyService
from aurum.modules.terceros.domain.party import PartyKind
from aurum.modules.terceros.infrastructure.repositories import SqlAlchemyPartyRepository
from aurum.modules.terceros.presentation.schemas import (
    CreatePartyRequest,
    PartyKpisResponse,
    PartyResponse,
    UpdatePartyRequest,
)
from aurum.shared.dependencies import get_session, require_tenant_id


def _service(session: AsyncSession, tenant_id: uuid.UUID, kind: PartyKind) -> PartyService:
    return PartyService(
        tenant_id=tenant_id,
        kind=kind,
        parties=SqlAlchemyPartyRepository(session),
    )


def build_parties_router(
    kind: PartyKind, *, prefix: str, tag: str, permission_resource: str
) -> APIRouter:
    """Construye el router CRUD de un tipo de tercero con sus guards de permiso.

    ``permission_resource`` es el recurso del catálogo RBAC (en plural: ``customers``
    / ``suppliers``), distinto del ``kind`` singular de la fila (``customer`` /
    ``supplier``).
    """
    router = APIRouter(prefix=prefix, tags=[tag])
    read_guard = Depends(require_permission(f"{permission_resource}:access"))
    write_guard = Depends(require_permission(f"{permission_resource}:manage"))
    write_dep = require_permission(f"{permission_resource}:manage")

    @router.get("", response_model=list[PartyResponse], dependencies=[read_guard])
    async def list_parties(
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
        include_deleted: bool = Query(default=False),
    ) -> list[PartyResponse]:
        views = await _service(session, tenant_id, kind).list(include_deleted=include_deleted)
        return [PartyResponse.from_view(v) for v in views]

    @router.get("/kpis", response_model=PartyKpisResponse, dependencies=[read_guard])
    async def parties_kpis(
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
    ) -> PartyKpisResponse:
        return PartyKpisResponse.from_view(await _service(session, tenant_id, kind).kpis())

    @router.get("/{party_id}", response_model=PartyResponse, dependencies=[read_guard])
    async def get_party(
        party_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
    ) -> PartyResponse:
        view = await _service(session, tenant_id, kind).get(party_id)
        return PartyResponse.from_view(view)

    @router.post(
        "",
        response_model=PartyResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[write_guard],
    )
    async def create_party(
        payload: CreatePartyRequest,
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
    ) -> PartyResponse:
        view = await _service(session, tenant_id, kind).create(payload.to_new_party())
        return PartyResponse.from_view(view)

    @router.patch("/{party_id}", response_model=PartyResponse, dependencies=[write_guard])
    async def update_party(
        party_id: uuid.UUID,
        payload: UpdatePartyRequest,
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
    ) -> PartyResponse:
        view = await _service(session, tenant_id, kind).update(party_id, payload.to_patch())
        return PartyResponse.from_view(view)

    @router.delete("/{party_id}", response_model=PartyResponse, dependencies=[write_guard])
    async def delete_party(
        party_id: uuid.UUID,
        request: Request,
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
        principal: Principal = Depends(write_dep),
    ) -> PartyResponse:
        view = await _service(session, tenant_id, kind).delete(party_id)
        await record_event(
            session, tenant_id, action=PARTY_DELETE, entity_type=kind,
            entity_id=party_id, principal=principal, request=request,
            changes={"legal_name": view.legal_name},
        )
        return PartyResponse.from_view(view)

    @router.post(
        "/{party_id}/restore", response_model=PartyResponse, dependencies=[write_guard]
    )
    async def restore_party(
        party_id: uuid.UUID,
        request: Request,
        session: AsyncSession = Depends(get_session),
        tenant_id: uuid.UUID = Depends(require_tenant_id),
        principal: Principal = Depends(write_dep),
    ) -> PartyResponse:
        view = await _service(session, tenant_id, kind).restore(party_id)
        await record_event(
            session, tenant_id, action=PARTY_RESTORE, entity_type=kind,
            entity_id=party_id, principal=principal, request=request,
        )
        return PartyResponse.from_view(view)

    return router


customers_router = build_parties_router(
    "customer", prefix="/customers", tag="customers", permission_resource="customers"
)
suppliers_router = build_parties_router(
    "supplier", prefix="/suppliers", tag="suppliers", permission_resource="suppliers"
)
