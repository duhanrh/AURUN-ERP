"""Implementación SQLAlchemy del puerto de Auditoría."""

from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.application.dto import AuditFilters
from aurum.modules.audit.infrastructure.models import AuditLog

_MAX_ROWS = 500


class SqlAlchemyAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, log: AuditLog) -> AuditLog:
        self._session.add(log)
        await self._session.flush()
        return log

    async def list(self, filters: AuditFilters) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(_MAX_ROWS)
        if filters.date_from is not None:
            stmt = stmt.where(AuditLog.created_at >= datetime.combine(filters.date_from, time.min))
        if filters.date_to is not None:
            stmt = stmt.where(AuditLog.created_at <= datetime.combine(filters.date_to, time.max))
        if filters.user_id is not None:
            stmt = stmt.where(AuditLog.user_id == filters.user_id)
        if filters.entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == filters.entity_type)
        if filters.action is not None:
            stmt = stmt.where(AuditLog.action == filters.action)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
