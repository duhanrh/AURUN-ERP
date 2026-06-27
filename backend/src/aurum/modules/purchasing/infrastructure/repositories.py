"""Implementación SQLAlchemy del puerto de Compras."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.purchasing.infrastructure.models import PurchaseOrder


class SqlAlchemyPurchaseOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[PurchaseOrder]:
        result = await self._session.execute(
            select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, order_id: uuid.UUID) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def add(self, order: PurchaseOrder) -> PurchaseOrder:
        self._session.add(order)
        await self._session.flush()
        return order
