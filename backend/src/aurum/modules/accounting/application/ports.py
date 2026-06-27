"""Puertos (Protocols) del módulo de Contabilidad."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.accounting.infrastructure.models import ChartAccount, JournalEntry


class AccountRepository(Protocol):
    async def list_all(self) -> list[ChartAccount]: ...
    async def get_by_code(self, code: str) -> ChartAccount | None: ...


class JournalEntryRepository(Protocol):
    async def list_all(self) -> list[JournalEntry]: ...
    async def get(self, entry_id: uuid.UUID) -> JournalEntry | None: ...
    async def add(self, entry: JournalEntry) -> JournalEntry: ...
