"""DTOs del módulo de API pública / API Keys."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ApiKeyView:
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class CreatedApiKey:
    key: ApiKeyView
    full_key: str  # se muestra una sola vez


@dataclass(frozen=True, slots=True)
class NewApiKey:
    name: str
    scopes: list[str]


@dataclass(frozen=True, slots=True)
class ApiKeyContext:
    tenant_id: uuid.UUID
    prefix: str
    scopes: frozenset[str]
