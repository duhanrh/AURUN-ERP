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
        """Materiales operativos (activos y no eliminados) — fuente de los selectores."""
        result = await self._session.execute(
            select(Material)
            .where(Material.is_active.is_(True), Material.deleted_at.is_(None))
            .order_by(Material.name)
        )
        return list(result.scalars().all())

    async def list_catalog(self, *, include_deleted: bool = False) -> list[Material]:
        """Catálogo completo para gestión (incluye inactivos; opcional eliminados)."""
        stmt = select(Material)
        if not include_deleted:
            stmt = stmt.where(Material.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(Material.name))
        return list(result.scalars().all())

    async def get(
        self, material_id: uuid.UUID, *, include_deleted: bool = False
    ) -> Material | None:
        stmt = select(Material).where(Material.id == material_id)
        if not include_deleted:
            stmt = stmt.where(Material.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_code(self, code: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = (
            select(func.count())
            .select_from(Material)
            .where(func.lower(Material.code) == code.lower(), Material.deleted_at.is_(None))
        )
        if exclude_id is not None:
            stmt = stmt.where(Material.id != exclude_id)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def add(self, material: Material) -> Material:
        self._session.add(material)
        await self._session.flush()
        return material


class SqlAlchemyLotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, *, include_deleted: bool = False) -> list[InventoryLot]:
        stmt = select(InventoryLot)
        if not include_deleted:
            stmt = stmt.where(InventoryLot.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(InventoryLot.created_at.desc()))
        return list(result.scalars().all())

    async def get(self, lot_id: uuid.UUID, *, include_deleted: bool = False) -> InventoryLot | None:
        stmt = select(InventoryLot).where(InventoryLot.id == lot_id)
        if not include_deleted:
            stmt = stmt.where(InventoryLot.deleted_at.is_(None))
        result = await self._session.execute(stmt)
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
            select(func.count()).select_from(InventoryLot).where(InventoryLot.lot_code == lot_code)
        )
        return (result.scalar() or 0) > 0
