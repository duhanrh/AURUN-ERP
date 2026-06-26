"""API de plataforma: provisionamiento de tenants (sección 5.7).

Protegida por un token de administrador de plataforma (cabecera
``X-Platform-Admin-Token``). En ``local`` con el token sin configurar, el endpoint
queda abierto para facilitar el arranque; fuera de ``local`` el token es
obligatorio.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.auth.infrastructure.security import hash_password
from aurum.modules.tenants.application.provisioning import NewTenant, ProvisioningService
from aurum.modules.tenants.presentation.schemas import (
    ProvisionTenantRequest,
    ProvisionTenantResponse,
)
from aurum.shared.config import Settings, get_settings
from aurum.shared.dependencies import get_session
from aurum.shared.errors import AuthorizationError

router = APIRouter(prefix="/platform", tags=["platform"])


def require_platform_admin(
    x_platform_admin_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.platform_admin_token
    if not expected:
        if settings.env != "local":
            raise AuthorizationError("La API de plataforma requiere un token configurado.")
        return  # local sin token configurado => abierto para bootstrap
    if x_platform_admin_token != expected:
        raise AuthorizationError("Token de administrador de plataforma inválido.")


@router.post(
    "/tenants",
    response_model=ProvisionTenantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def provision_tenant(
    payload: ProvisionTenantRequest,
    session: AsyncSession = Depends(get_session),
) -> ProvisionTenantResponse:
    service = ProvisioningService(session, password_hasher=hash_password)
    result = await service.provision(
        NewTenant(
            name=payload.name,
            subdomain=payload.subdomain,
            admin_email=payload.admin_email,
            admin_full_name=payload.admin_full_name,
            subscription_plan=payload.subscription_plan,
            admin_password=payload.admin_password,
        )
    )
    return ProvisionTenantResponse(
        tenant_id=result.tenant_id,
        subdomain=result.subdomain,
        admin_email=result.admin_email,
        admin_user_id=result.admin_user_id,
        initial_password=result.initial_password,
        roles_created=result.roles_created,
    )
