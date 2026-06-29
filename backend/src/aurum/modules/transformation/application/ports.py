"""Puertos del módulo de Transformación."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.transformation.infrastructure.models import TransformationOrder


class TransformationOrderRepository(Protocol):
    async def list_all(self, *, include_deleted: bool = False) -> list[TransformationOrder]: ...
    async def get(
        self, order_id: uuid.UUID, *, include_deleted: bool = False
    ) -> TransformationOrder | None: ...
    async def add(self, order: TransformationOrder) -> TransformationOrder: ...
