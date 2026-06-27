"""Puertos del módulo de Ventas."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.sales.infrastructure.models import SalesOrder


class SalesOrderRepository(Protocol):
    async def list_all(self) -> list[SalesOrder]: ...
    async def get(self, order_id: uuid.UUID) -> SalesOrder | None: ...
    async def add(self, order: SalesOrder) -> SalesOrder: ...
