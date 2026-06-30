"""Casos de uso de API Keys: gestión por el tenant y autenticación de la API pública."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aurum.modules.publicapi.application.dto import (
    ApiKeyContext,
    ApiKeyView,
    CreatedApiKey,
    NewApiKey,
)
from aurum.modules.publicapi.application.ports import ApiKeyRepository
from aurum.modules.publicapi.domain.keys import (
    generate_api_key,
    parse_api_key,
    valid_scopes,
    verify_secret,
)
from aurum.modules.publicapi.infrastructure.models import ApiKey
from aurum.shared.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
)


class InvalidApiKeyError(AuthenticationError):
    error_code = "invalid_api_key"


class MissingScopeError(AuthorizationError):
    error_code = "insufficient_scope"


def _to_view(key: ApiKey) -> ApiKeyView:
    return ApiKeyView(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        scopes=list(key.scopes),
        is_active=key.is_active,
        last_used_at=key.last_used_at,
        revoked_at=key.revoked_at,
        created_at=key.created_at,
    )


class ApiKeyService:
    """Gestión de las API Keys del tenant (requiere sesión interactiva con permiso)."""

    def __init__(self, *, tenant_id: uuid.UUID, keys: ApiKeyRepository) -> None:
        self._tenant_id = tenant_id
        self._keys = keys

    async def create(self, data: NewApiKey) -> CreatedApiKey:
        if not valid_scopes(data.scopes):
            raise ConflictError("Scopes inválidos o vacíos para la API Key.")
        full_key, prefix, secret_hash = generate_api_key()
        key = ApiKey(
            tenant_id=self._tenant_id,
            name=data.name,
            prefix=prefix,
            secret_hash=secret_hash,
            scopes=data.scopes,
            is_active=True,
        )
        await self._keys.add(key)
        return CreatedApiKey(key=_to_view(key), full_key=full_key)

    async def list(self) -> list[ApiKeyView]:
        return [_to_view(k) for k in await self._keys.list_for_tenant(self._tenant_id)]

    async def revoke(self, key_id: uuid.UUID) -> ApiKeyView:
        key = await self._keys.get_for_tenant(self._tenant_id, key_id)
        if key is None:
            raise NotFoundError("API Key no encontrada.")
        key.is_active = False
        key.revoked_at = datetime.now(UTC).replace(tzinfo=None)
        return _to_view(key)


async def authenticate_api_key(
    keys: ApiKeyRepository, full_key: str, *, required_scope: str
) -> ApiKeyContext:
    """Resuelve y valida una API Key entrante (sin tenant previo)."""
    parsed = parse_api_key(full_key)
    if parsed is None:
        raise InvalidApiKeyError("Formato de API Key inválido.")
    prefix, secret = parsed
    key = await keys.get_by_prefix(prefix)
    if key is None or not key.is_active or not verify_secret(secret, key.secret_hash):
        raise InvalidApiKeyError("API Key inválida o revocada.")
    if required_scope not in key.scopes:
        raise MissingScopeError(f"La API Key no tiene el scope '{required_scope}'.")
    key.last_used_at = datetime.now(UTC).replace(tzinfo=None)
    return ApiKeyContext(tenant_id=key.tenant_id, prefix=key.prefix, scopes=frozenset(key.scopes))
