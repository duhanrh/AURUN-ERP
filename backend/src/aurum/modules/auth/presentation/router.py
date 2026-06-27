"""Endpoints de Autenticación: login, refresh, logout y perfil del usuario."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import AUTH_LOGIN_FAILED
from aurum.modules.audit.presentation.recorder import record_event_isolated
from aurum.modules.auth.application.services import AuthService
from aurum.modules.auth.infrastructure import login_guard
from aurum.modules.auth.infrastructure.repositories import (
    SqlAlchemyRefreshTokenRepository,
)
from aurum.modules.auth.presentation.dependencies import (
    Principal,
    get_current_principal,
)
from aurum.modules.auth.presentation.schemas import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    TokenResponse,
)
from aurum.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from aurum.shared.dependencies import get_session, require_tenant_id
from aurum.shared.errors import AuthenticationError, DomainError


class TooManyAttemptsError(DomainError):
    status_code = 429
    error_code = "too_many_attempts"

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(session: AsyncSession, tenant_id: uuid.UUID) -> AuthService:
    return AuthService(
        tenant_id=tenant_id,
        session=session,
        users=SqlAlchemyUserRepository(session),
        refresh_tokens=SqlAlchemyRefreshTokenRepository(session),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TokenResponse:
    guard_key = f"{tenant_id}:{payload.email.lower()}"
    if login_guard.is_blocked(guard_key):
        # Bloqueo temporal anti fuerza bruta (sección 10): demasiados fallos.
        await record_event_isolated(
            tenant_id,
            action=AUTH_LOGIN_FAILED,
            entity_type="auth",
            request=request,
            changes={"email": payload.email, "blocked": True},
        )
        raise TooManyAttemptsError("Demasiados intentos fallidos; inténtalo más tarde.")
    try:
        pair = await _build_service(session, tenant_id).login(payload.email, payload.password)
    except AuthenticationError:
        login_guard.record_failure(guard_key)
        # Acceso fallido: se audita en una transacción propia (sección 7.18) porque
        # la de la petición se revierte al propagar el 401.
        await record_event_isolated(
            tenant_id,
            action=AUTH_LOGIN_FAILED,
            entity_type="auth",
            request=request,
            changes={"email": payload.email},
        )
        raise
    login_guard.reset(guard_key)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TokenResponse:
    pair = await _build_service(session, tenant_id).refresh(payload.refresh_token)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    _: Principal = Depends(get_current_principal),
) -> None:
    await _build_service(session, tenant_id).logout(payload.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(principal: Principal = Depends(get_current_principal)) -> MeResponse:
    return MeResponse(
        user_id=principal.user_id,
        tenant_id=principal.tenant_id,
        role=principal.role,
        permissions=sorted(principal.permissions),
    )
