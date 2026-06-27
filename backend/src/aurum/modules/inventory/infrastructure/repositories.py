"""Implementaciones SQLAlchemy de los puertos del Inventario.

Operan dentro de una sesión ya acotada al tenant por RLS (``get_session``); el
aislamiento lo impone la base (sección 5.5).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.inventory.infrastructure.models import InventoryLot, Material


class SqlAlchemyMaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Material]:
        result = await self._session.execute(
            select(Material).where(Material.is_active.is_(True)).order_by(Material.name)
        )
        return list(result.scalars().all())

    async def get(self, material_id: uuid.UUID) -> Material | None:
        result = await self._session.execute(select(Material).where(Material.id == material_id))
        return result.scalar_one_or_none()


class SqlAlchemyLotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[InventoryLot]:
        result = await self._session.execute(
            select(InventoryLot).order_by(InventoryLot.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, lot_id: uuid.UUID) -> InventoryLot | None:
        result = await self._session.execute(
            select(InventoryLot).where(InventoryLot.id == lot_id)
        )
        return result.scalar_one_or_none()

    async def add(self, lot: InventoryLot) -> InventoryLot:
        self._session.add(lot)
        await self._session.flush()
        return lot

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(InventoryLot))
        return result.scalar() or 0

    async def exists_code(self, lot_code: str) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(InventoryLot)
            .where(InventoryLot.lot_code == lot_code)
        )
        return (result.scalar() or 0) > 0
