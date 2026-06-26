"""Endpoints de Autenticación: login, refresh, logout y perfil del usuario."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.application.services import AuthService
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
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> TokenResponse:
    pair = await _build_service(session, tenant_id).login(payload.email, payload.password)
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
