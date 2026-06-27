"""Dependencias de la API pública: autenticación por API Key + rate limiting + RLS.

A diferencia de la API interna (JWT de sesión), aquí el tenant se resuelve **de la
propia API Key**. Tras validar la clave y el scope, se aplica el tenant a la sesión
(``set_config``) para que todas las consultas de datos pasen por RLS como el resto
del sistema (sección 7.19).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from fastapi import Header
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.publicapi.application.dto import ApiKeyContext
from aurum.modules.publicapi.application.services import authenticate_api_key
from aurum.modules.publicapi.infrastructure.ratelimit import check_rate_limit
from aurum.modules.publicapi.infrastructure.repositories import SqlAlchemyApiKeyRepository
from aurum.shared.errors import DomainError
from aurum.shared.infrastructure.database import get_session_factory


class RateLimitError(DomainError):
    status_code = 429
    error_code = "rate_limited"


def public_session(
    required_scope: str,
) -> Callable[[str | None], AsyncIterator[tuple[AsyncSession, ApiKeyContext]]]:
    """Construye una dependencia que exige una API Key válida con ``required_scope``."""

    async def _dependency(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> AsyncIterator[tuple[AsyncSession, ApiKeyContext]]:
        from aurum.modules.publicapi.application.services import InvalidApiKeyError

        if not x_api_key:
            raise InvalidApiKeyError("Falta la cabecera X-API-Key.")
        factory = get_session_factory()
        async with factory() as session:
            repo = SqlAlchemyApiKeyRepository(session)
            context = await authenticate_api_key(repo, x_api_key, required_scope=required_scope)
            if not check_rate_limit(context.prefix):
                raise RateLimitError("Límite de peticiones excedido para esta API Key.")
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(context.tenant_id)},
            )
            try:
                yield session, context
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return _dependency
