"""Implementación SQLAlchemy de los puertos de Contabilidad."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.infrastructure.models import ChartAccount, JournalEntry


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[ChartAccount]:
        result = await self._session.execute(
            select(ChartAccount).order_by(ChartAccount.code)
        )
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> ChartAccount | None:
        result = await self._session.execute(
            select(ChartAccount).where(ChartAccount.code == code)
        )
        return result.scalar_one_or_none()


class SqlAlchemyJournalEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[JournalEntry]:
        result = await self._session.execute(
            select(JournalEntry).order_by(
                JournalEntry.entry_date.desc(), JournalEntry.created_at.desc()
            )
        )
        return list(result.scalars().all())

    async def get(self, entry_id: uuid.UUID) -> JournalEntry | None:
        result = await self._session.execute(
            select(JournalEntry).where(JournalEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def add(self, entry: JournalEntry) -> JournalEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry
