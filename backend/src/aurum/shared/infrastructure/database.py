"""Motor y sesiones de SQLAlchemy (async) + aplicación de RLS por transacción.

Punto único donde se inyecta el ``tenant_id`` a la sesión de base de datos vía
``SET LOCAL app.current_tenant_id`` (sección 5.5). Al ser ``SET LOCAL`` queda
acotado a la transacción y es seguro con PgBouncer en modo ``transaction``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from aurum.shared.config import get_settings
from aurum.shared.tenant_context import get_current_tenant_id

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Devuelve el engine async (singleton perezoso)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def _apply_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Fija el tenant de la transacción para que RLS filtre las filas.

    Se usa ``set_config(clave, valor, is_local=true)`` (equivalente a ``SET LOCAL``)
    porque, a diferencia de ``SET``, admite parámetros enlazados — necesario con
    asyncpg, que no permite ``SET ... = $1``.
    """
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI: abre una sesión con el tenant aplicado.

    Hace commit al terminar sin error y rollback ante excepción. Se gestiona la
    transacción manualmente (en vez de ``session.begin()``) para permitir que un
    caso de uso confirme un efecto de seguridad —p. ej. revocar una sesión ante
    reutilización de refresh token— aunque después se propague un 401.
    """
    factory = get_session_factory()
    async with factory() as session:
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            await _apply_tenant(session, tenant_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Cierra el engine (usar en el shutdown de la app)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
