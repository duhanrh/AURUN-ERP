"""Esquemas Pydantic de gestión de API Keys (sección 7.19)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from aurum.modules.publicapi.application.dto import (
    ApiKeyView,
    CreatedApiKey,
    NewApiKey,
)
from aurum.modules.publicapi.domain.keys import SCOPES


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, v: ApiKeyView) -> ApiKeyResponse:
        return cls(
            id=v.id,
            name=v.name,
            prefix=v.prefix,
            scopes=v.scopes,
            is_active=v.is_active,
            last_used_at=v.last_used_at,
            revoked_at=v.revoked_at,
            created_at=v.created_at,
        )


class CreatedApiKeyResponse(BaseModel):
    """Incluye la clave completa, que solo se muestra una vez."""

    key: ApiKeyResponse
    full_key: str

    @classmethod
    def from_view(cls, v: CreatedApiKey) -> CreatedApiKeyResponse:
        return cls(key=ApiKeyResponse.from_view(v.key), full_key=v.full_key)


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1)

    def to_dto(self) -> NewApiKey:
        return NewApiKey(name=self.name, scopes=self.scopes)


class AvailableScopesResponse(BaseModel):
    scopes: list[str]

    @classmethod
    def all(cls) -> AvailableScopesResponse:
        return cls(scopes=list(SCOPES))
