"""Puertos (Protocols) del módulo de Terceros — contratos de persistencia."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.terceros.domain.party import PartyKind
from aurum.modules.terceros.infrastructure.models import Party


class PartyRepository(Protocol):
    async def list_by_kind(self, kind: PartyKind) -> list[Party]: ...
    async def get(self, kind: PartyKind, party_id: uuid.UUID) -> Party | None: ...
    async def exists_tax_id(
        self, kind: PartyKind, tax_id: str, *, exclude_id: uuid.UUID | None = None
    ) -> bool: ...
    async def add(self, party: Party) -> Party: ...
    async def count_by_status(self, kind: PartyKind) -> dict[str, int]: ...
