"""Implementación SQLAlchemy del puerto de Calidad."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.quality.infrastructure.models import QualitySample


class SqlAlchemyQualitySampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, include_deleted: bool = False) -> list[QualitySample]:
        stmt = select(QualitySample)
        if not include_deleted:
            stmt = stmt.where(QualitySample.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(QualitySample.created_at.desc()))
        return list(result.scalars().all())

    async def get(
        self, sample_id: uuid.UUID, *, include_deleted: bool = False
    ) -> QualitySample | None:
        stmt = select(QualitySample).where(QualitySample.id == sample_id)
        if not include_deleted:
            stmt = stmt.where(QualitySample.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, sample: QualitySample) -> QualitySample:
        self._session.add(sample)
        await self._session.flush()
        return sample
