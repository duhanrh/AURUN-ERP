"""Gestión de API Keys del tenant (Configuración → API Keys, sección 7.19).

Usa la sesión interactiva (JWT). Lectura con ``configuration:access``; crear/revocar
con ``configuration:manage``. La clave completa se devuelve **una sola vez** al crearla.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.modules.publicapi.application.services import ApiKeyService
from aurum.modules.publicapi.infrastructure.repositories import SqlAlchemyApiKeyRepository
from aurum.modules.publicapi.presentation.schemas import (
    ApiKeyResponse,
    AvailableScopesResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/configuration/api-keys", tags=["api-keys"])

_read = Depends(require_permission("configuration:access"))
_manage = Depends(require_permission("configuration:manage"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> ApiKeyService:
    return ApiKeyService(tenant_id=tenant_id, keys=SqlAlchemyApiKeyRepository(session))


@router.get("/scopes", response_model=AvailableScopesResponse, dependencies=[_read])
async def available_scopes() -> AvailableScopesResponse:
    return AvailableScopesResponse.all()


@router.get("", response_model=list[ApiKeyResponse], dependencies=[_read])
async def list_keys(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[ApiKeyResponse]:
    return [ApiKeyResponse.from_view(v) for v in await _service(session, tenant_id).list()]


@router.post(
    "",
    response_model=CreatedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage],
)
async def create_key(
    payload: CreateApiKeyRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> CreatedApiKeyResponse:
    created = await _service(session, tenant_id).create(payload.to_dto())
    return CreatedApiKeyResponse.from_view(created)


@router.delete("/{key_id}", response_model=ApiKeyResponse, dependencies=[_manage])
async def revoke_key(
    key_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> ApiKeyResponse:
    return ApiKeyResponse.from_view(await _service(session, tenant_id).revoke(key_id))
