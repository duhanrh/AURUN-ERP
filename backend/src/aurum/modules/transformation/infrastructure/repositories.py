"""Implementación SQLAlchemy del puerto de Transformación."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.transformation.infrastructure.models import TransformationOrder


class SqlAlchemyTransformationOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, include_deleted: bool = False) -> list[TransformationOrder]:
        stmt = select(TransformationOrder)
        if not include_deleted:
            stmt = stmt.where(TransformationOrder.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(TransformationOrder.created_at.desc()))
        return list(result.scalars().all())

    async def get(
        self, order_id: uuid.UUID, *, include_deleted: bool = False
    ) -> TransformationOrder | None:
        stmt = select(TransformationOrder).where(TransformationOrder.id == order_id)
        if not include_deleted:
            stmt = stmt.where(TransformationOrder.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, order: TransformationOrder) -> TransformationOrder:
        self._session.add(order)
        await self._session.flush()
        return order
