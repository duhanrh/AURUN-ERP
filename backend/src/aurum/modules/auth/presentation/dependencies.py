"""Dependencias de FastAPI para autenticación y autorización (RBAC).

- ``get_current_principal``: decodifica y valida el access JWT del header
  ``Authorization: Bearer``; expone el sujeto autenticado.
- ``require_permission(code)``: factory de dependencia que exige un permiso
  efectivo concreto; la comprobación ocurre en el servidor (sección 10.2), no solo
  en la UI.

El ``tenant_id`` del token debe coincidir con el tenant resuelto por el middleware
(que ya fijó el contexto RLS): cualquier discrepancia es un 401.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aurum.modules.auth.infrastructure.security import TokenService
from aurum.shared.errors import AuthenticationError, AuthorizationError
from aurum.shared.tenant_context import get_current_tenant_id

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class Principal:
    """Sujeto autenticado derivado del access token."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str | None
    permissions: frozenset[str]
    jti: str

    def has(self, permission: str) -> bool:
        return permission in self.permissions


def get_token_service() -> TokenService:
    return TokenService()


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tokens: TokenService = Depends(get_token_service),
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Falta el token de acceso.")
    try:
        claims = tokens.decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Token de acceso inválido o expirado.") from exc

    context_tenant = get_current_tenant_id()
    if context_tenant is not None and context_tenant != claims.tenant_id:
        raise AuthenticationError("El tenant del token no coincide con la petición.")

    principal = Principal(
        user_id=claims.user_id,
        tenant_id=claims.tenant_id,
        role=claims.role,
        permissions=frozenset(claims.permissions),
        jti=claims.jti,
    )
    request.state.principal = principal
    return principal


def require_permission(permission: str):  # type: ignore[no-untyped-def]
    """Devuelve una dependencia que exige ``permission`` en el principal."""

    async def _dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if not principal.has(permission):
            raise AuthorizationError(f"Permiso requerido: {permission}.")
        return principal

    return _dependency
