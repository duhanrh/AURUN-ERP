"""Implementación SQLAlchemy del puerto de Ventas."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.sales.infrastructure.models import SalesOrder


class SqlAlchemySalesOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, include_deleted: bool = False) -> list[SalesOrder]:
        stmt = select(SalesOrder)
        if not include_deleted:
            stmt = stmt.where(SalesOrder.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(SalesOrder.created_at.desc()))
        return list(result.scalars().all())

    async def get(self, order_id: uuid.UUID, *, include_deleted: bool = False) -> SalesOrder | None:
        stmt = select(SalesOrder).where(SalesOrder.id == order_id)
        if not include_deleted:
            stmt = stmt.where(SalesOrder.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, order: SalesOrder) -> SalesOrder:
        self._session.add(order)
        await self._session.flush()
        return order
