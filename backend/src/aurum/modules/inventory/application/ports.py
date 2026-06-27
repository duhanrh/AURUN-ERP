"""Puertos (Protocols) del módulo de Inventario.

``LotRepository`` lo consumen también Compras (al aprobar una OC se registra un lote)
y Ventas (al vender se consume stock), de modo que es el contrato de integración
entre los tres módulos de operación sin acoplarlos a SQLAlchemy.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.inventory.infrastructure.models import InventoryLot, Material


class MaterialRepository(Protocol):
    async def list_active(self) -> list[Material]: ...
    async def get(self, material_id: uuid.UUID) -> Material | None: ...


class LotRepository(Protocol):
    async def list_all(self) -> list[InventoryLot]: ...
    async def get(self, lot_id: uuid.UUID) -> InventoryLot | None: ...
    async def add(self, lot: InventoryLot) -> InventoryLot: ...
    async def count(self) -> int: ...
    async def exists_code(self, lot_code: str) -> bool: ...
