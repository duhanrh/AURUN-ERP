"""Implementación SQLAlchemy del puerto de API Keys.

``api_keys`` es tabla de plataforma (sin RLS): la gestión filtra por ``tenant_id``
explícitamente y la autenticación busca por ``prefix`` (sin tenant aún resuelto).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.publicapi.infrastructure.models import ApiKey


class SqlAlchemyApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, key: ApiKey) -> ApiKey:
        self._session.add(key)
        await self._session.flush()
        return key

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_tenant(self, tenant_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKey).where(ApiKey.tenant_id == tenant_id, ApiKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_prefix(self, prefix: str) -> ApiKey | None:
        result = await self._session.execute(select(ApiKey).where(ApiKey.prefix == prefix))
        return result.scalar_one_or_none()
