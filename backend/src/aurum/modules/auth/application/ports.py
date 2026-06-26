"""Puertos del módulo de Autenticación."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.auth.infrastructure.models import RefreshToken


class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> RefreshToken: ...
    async def get_by_jti(self, jti: str) -> RefreshToken | None: ...
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None: ...
