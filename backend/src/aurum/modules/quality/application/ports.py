"""Puertos del módulo de Calidad."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.quality.infrastructure.models import QualitySample


class QualitySampleRepository(Protocol):
    async def list_all(self) -> list[QualitySample]: ...
    async def get(self, sample_id: uuid.UUID) -> QualitySample | None: ...
    async def add(self, sample: QualitySample) -> QualitySample: ...
