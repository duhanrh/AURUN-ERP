"""Endpoints de Auditoría (``/audit``): consulta filtrada del registro (7.18).

Solo lectura (no hay alta/edición/borrado por API; el log es append-only). Lectura
reservada a roles altos vía ``audit:access``. Filtros por fecha, usuario, entidad
y acción, siempre acotados al tenant por RLS.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.application.dto import AuditFilters
from aurum.modules.audit.application.services import AuditService
from aurum.modules.audit.infrastructure.repositories import SqlAlchemyAuditRepository
from aurum.modules.audit.presentation.schemas import AuditLogResponse
from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/audit", tags=["audit"])

_read = Depends(require_permission("audit:access"))


@router.get("", response_model=list[AuditLogResponse], dependencies=[_read])
async def list_audit(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
) -> list[AuditLogResponse]:
    service = AuditService(tenant_id=tenant_id, logs=SqlAlchemyAuditRepository(session))
    filters = AuditFilters(
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        entity_type=entity_type,
        action=action,
    )
    return [AuditLogResponse.from_view(v) for v in await service.list(filters)]
