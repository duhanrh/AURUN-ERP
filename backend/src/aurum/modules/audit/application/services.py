"""Casos de uso de Auditoría: registrar eventos y consultarlos con filtros (7.18)."""

from __future__ import annotations

import uuid

from aurum.modules.audit.application.dto import AuditFilters, AuditLogView, NewAuditEvent
from aurum.modules.audit.application.ports import AuditRepository
from aurum.modules.audit.infrastructure.models import AuditLog


class AuditService:
    def __init__(self, *, tenant_id: uuid.UUID, logs: AuditRepository) -> None:
        self._tenant_id = tenant_id
        self._logs = logs

    async def record(self, event: NewAuditEvent) -> None:
        log = AuditLog(
            tenant_id=self._tenant_id,
            user_id=event.user_id,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            changes=event.changes,
            ip_address=event.ip_address,
        )
        await self._logs.add(log)

    async def list(self, filters: AuditFilters) -> list[AuditLogView]:
        return [_to_view(log) for log in await self._logs.list(filters)]


def _to_view(log: AuditLog) -> AuditLogView:
    return AuditLogView(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        changes=log.changes,
        ip_address=log.ip_address,
        created_at=log.created_at,
    )
