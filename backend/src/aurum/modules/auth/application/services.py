"""Casos de uso de Autenticación: login, rotación de refresh y logout.

Flujo (secciones 10.1/10.4):
- ``login``: valida credenciales (argon2), emite access JWT (~15 min) + refresh
  token persistido (hash) y actualiza ``last_login_at``.
- ``refresh``: rota el refresh token (lo revoca y emite uno nuevo encadenado). Si
  llega un refresh ya revocado => posible robo: se revocan **todos** los del
  usuario y se rechaza.
- ``logout``: revoca el refresh token de la sesión.

Las contraseñas se verifican con tiempo constante por passlib; ante usuario
inexistente igualmente se responde de forma genérica para no filtrar qué emails
existen.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.application.dto import TokenPair
from aurum.modules.auth.application.ports import RefreshTokenRepository
from aurum.modules.auth.infrastructure.models import RefreshToken
from aurum.modules.auth.infrastructure.security import (
    AccessTokenClaims,
    TokenService,
    verify_password,
)
from aurum.modules.users.application.ports import UserRepository
from aurum.modules.users.domain.authorization import compute_effective_permissions
from aurum.modules.users.infrastructure.models import User
from aurum.shared.config import get_settings
from aurum.shared.errors import AuthenticationError


def _now() -> datetime:
    """Instante actual en UTC *naïve* (las columnas son ``TIMESTAMP`` sin tz)."""
    return datetime.now(tz=UTC).replace(tzinfo=None)


def _effective_permissions(user: User) -> frozenset[str]:
    role_codes = [p.code for p in user.role.permissions] if user.role else []
    granted = [e.permission.code for e in user.exceptions if e.granted]
    revoked = [e.permission.code for e in user.exceptions if not e.granted]
    return compute_effective_permissions(role_codes, granted, revoked)


class AuthService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        session: AsyncSession,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        token_service: TokenService | None = None,
    ) -> None:
        self._tenant_id = tenant_id
        self._session = session
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._tokens = token_service or TokenService()

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Credenciales inválidas.")
        if not user.is_active:
            raise AuthenticationError("La cuenta está desactivada.")

        user.last_login_at = _now()
        pair, _ = await self._issue_tokens(user)
        return pair

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        jti = raw_refresh_token.split(".", 1)[0]
        stored = await self._refresh_tokens.get_by_jti(jti)
        token_hash = TokenService.hash_refresh_token(raw_refresh_token)

        if stored is None or stored.token_hash != token_hash:
            raise AuthenticationError("Refresh token inválido.")

        if stored.revoked_at is not None:
            # Reutilización de un token ya rotado => señal de robo (sección 10.1).
            # Se confirma la revocación de toda la cadena ANTES de propagar el 401,
            # para que el efecto de seguridad persista pese al rollback del error.
            await self._refresh_tokens.revoke_all_for_user(stored.user_id)
            await self._session.commit()
            raise AuthenticationError("Refresh token reutilizado; sesión revocada.")

        if stored.expires_at <= _now():
            raise AuthenticationError("Refresh token expirado.")

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario no disponible.")

        new_pair, new_token = await self._issue_tokens(user)
        stored.revoked_at = _now()
        stored.replaced_by_id = new_token.id
        return new_pair

    async def logout(self, raw_refresh_token: str) -> None:
        jti = raw_refresh_token.split(".", 1)[0]
        stored = await self._refresh_tokens.get_by_jti(jti)
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = _now()

    async def _issue_tokens(self, user: User) -> tuple[TokenPair, RefreshToken]:
        raw, jti, token_hash = TokenService.generate_refresh_token()
        refresh_row = RefreshToken(
            tenant_id=self._tenant_id,
            user_id=user.id,
            jti=jti,
            token_hash=token_hash,
            expires_at=_now() + timedelta(seconds=self._tokens.refresh_ttl_seconds),
        )
        await self._refresh_tokens.add(refresh_row)

        # El access token comparte el ``jti`` de la sesión (refresh) para permitir
        # revocación coordinada (logout): el access caduca en ~15 min de todos modos.
        access = self._tokens.issue_access_token(
            AccessTokenClaims(
                user_id=user.id,
                tenant_id=self._tenant_id,
                role=user.role.slug if user.role else None,
                permissions=tuple(sorted(_effective_permissions(user))),
                jti=jti,
            )
        )
        pair = TokenPair(
            access_token=access,
            refresh_token=raw,
            expires_in=get_settings().jwt_access_ttl_seconds,
        )
        return pair, refresh_row
