"""Puertos (Protocols) del módulo de Auditoría."""

from __future__ import annotations

from typing import Protocol

from aurum.modules.audit.application.dto import AuditFilters
from aurum.modules.audit.infrastructure.models import AuditLog


class AuditRepository(Protocol):
    async def add(self, log: AuditLog) -> AuditLog: ...
    async def list(self, filters: AuditFilters) -> list[AuditLog]: ...
