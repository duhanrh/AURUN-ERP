"""Implementación SQLAlchemy de los puertos de Configuración.

Los repos NO filtran por tenant: la RLS (políticas de la sección 5.5) garantiza
que cada consulta solo ve las filas del tenant del contexto. Por eso ``get()``
puede asumir una sola fila por tenant.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.config.infrastructure.models import (
    TenantBusinessParameters,
    TenantModuleConfig,
)
from aurum.modules.tenants.infrastructure.models import TenantBranding


class SqlAlchemyBrandingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> TenantBranding | None:
        result = await self._session.execute(select(TenantBranding))
        return result.scalar_one_or_none()


class SqlAlchemyParametersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> TenantBusinessParameters | None:
        result = await self._session.execute(select(TenantBusinessParameters))
        return result.scalar_one_or_none()


class SqlAlchemyModuleConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[TenantModuleConfig]:
        result = await self._session.execute(
            select(TenantModuleConfig).order_by(TenantModuleConfig.module_key)
        )
        return list(result.scalars().all())

    async def get(self, module_key: str) -> TenantModuleConfig | None:
        result = await self._session.execute(
            select(TenantModuleConfig).where(TenantModuleConfig.module_key == module_key)
        )
        return result.scalar_one_or_none()
