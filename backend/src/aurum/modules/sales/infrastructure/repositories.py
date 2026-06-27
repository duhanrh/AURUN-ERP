"""Implementación SQLAlchemy del puerto de Ventas."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.sales.infrastructure.models import SalesOrder


class SqlAlchemySalesOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[SalesOrder]:
        result = await self._session.execute(
            select(SalesOrder).order_by(SalesOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, order_id: uuid.UUID) -> SalesOrder | None:
        result = await self._session.execute(select(SalesOrder).where(SalesOrder.id == order_id))
        return result.scalar_one_or_none()

    async def add(self, order: SalesOrder) -> SalesOrder:
        self._session.add(order)
        await self._session.flush()
        return order
