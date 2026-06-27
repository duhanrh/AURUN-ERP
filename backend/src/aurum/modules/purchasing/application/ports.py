"""Puertos del módulo de Compras."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.purchasing.infrastructure.models import PurchaseOrder


class PurchaseOrderRepository(Protocol):
    async def list_all(self) -> list[PurchaseOrder]: ...
    async def get(self, order_id: uuid.UUID) -> PurchaseOrder | None: ...
    async def add(self, order: PurchaseOrder) -> PurchaseOrder: ...
