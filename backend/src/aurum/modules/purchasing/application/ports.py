"""Puertos del módulo de Compras."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.purchasing.infrastructure.models import PurchaseOrder


class PurchaseOrderRepository(Protocol):
    async def list_all(self, *, include_deleted: bool = False) -> list[PurchaseOrder]: ...
    async def get(
        self, order_id: uuid.UUID, *, include_deleted: bool = False
    ) -> PurchaseOrder | None: ...
    async def add(self, order: PurchaseOrder) -> PurchaseOrder: ...
