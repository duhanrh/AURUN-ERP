"""Implementación SQLAlchemy del puerto ``PartyRepository``.

Opera dentro de una sesión ya acotada al tenant por RLS (``get_session``), así que
las consultas no filtran ``tenant_id`` manualmente: la base lo impone (defensa en
profundidad, sección 5.5). El filtro por ``kind`` sí es responsabilidad de la app.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.terceros.domain.party import PartyKind
from aurum.modules.terceros.infrastructure.models import Party


class SqlAlchemyPartyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_kind(self, kind: PartyKind) -> list[Party]:
        result = await self._session.execute(
            select(Party).where(Party.kind == kind).order_by(Party.legal_name)
        )
        return list(result.scalars().all())

    async def get(self, kind: PartyKind, party_id: uuid.UUID) -> Party | None:
        result = await self._session.execute(
            select(Party).where(Party.id == party_id, Party.kind == kind)
        )
        return result.scalar_one_or_none()

    async def exists_tax_id(
        self, kind: PartyKind, tax_id: str, *, exclude_id: uuid.UUID | None = None
    ) -> bool:
        stmt = (
            select(func.count())
            .select_from(Party)
            .where(Party.kind == kind, func.lower(Party.tax_id) == tax_id.lower())
        )
        if exclude_id is not None:
            stmt = stmt.where(Party.id != exclude_id)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def add(self, party: Party) -> Party:
        self._session.add(party)
        await self._session.flush()
        return party

    async def count_by_status(self, kind: PartyKind) -> dict[str, int]:
        result = await self._session.execute(
            select(Party.status, func.count())
            .where(Party.kind == kind)
            .group_by(Party.status)
        )
        return {row[0]: row[1] for row in result.all()}
