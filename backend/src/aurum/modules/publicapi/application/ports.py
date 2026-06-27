"""Puertos (Protocols) del módulo de API pública."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.publicapi.infrastructure.models import ApiKey


class ApiKeyRepository(Protocol):
    async def add(self, key: ApiKey) -> ApiKey: ...
    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[ApiKey]: ...
    async def get_for_tenant(self, tenant_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey | None: ...
    async def get_by_prefix(self, prefix: str) -> ApiKey | None: ...
