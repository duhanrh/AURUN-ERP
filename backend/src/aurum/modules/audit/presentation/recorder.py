"""Helpers para registrar eventos de auditoría desde los puntos críticos.

``record_event`` escribe en la **misma** sesión/transacción de la petición (se
confirma con ella). ``record_event_isolated`` abre su **propia** sesión y confirma
de inmediato: necesario para auditar accesos fallidos, cuyo flujo termina en
excepción (la transacción de la petición se revierte).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.application.dto import NewAuditEvent
from aurum.modules.audit.application.services import AuditService
from aurum.modules.audit.infrastructure.repositories import SqlAlchemyAuditRepository
from aurum.modules.auth.presentation.dependencies import Principal
from aurum.shared.infrastructure.database import get_session_factory


def _client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


async def record_event(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    action: str,
    entity_type: str,
    principal: Principal | None = None,
    request: Request | None = None,
    entity_id: uuid.UUID | None = None,
    changes: dict[str, Any] | None = None,
) -> None:
    """Registra un evento en la transacción actual (se confirma con la petición)."""
    service = AuditService(tenant_id=tenant_id, logs=SqlAlchemyAuditRepository(session))
    await service.record(
        NewAuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            user_id=principal.user_id if principal is not None else None,
            ip_address=_client_ip(request),
        )
    )


async def record_event_isolated(
    tenant_id: uuid.UUID,
    *,
    action: str,
    entity_type: str,
    request: Request | None = None,
    changes: dict[str, Any] | None = None,
) -> None:
    """Registra un evento en una transacción propia (para accesos fallidos)."""
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        service = AuditService(tenant_id=tenant_id, logs=SqlAlchemyAuditRepository(session))
        await service.record(
            NewAuditEvent(
                action=action,
                entity_type=entity_type,
                ip_address=_client_ip(request),
                changes=changes,
            )
        )
        await session.commit()
