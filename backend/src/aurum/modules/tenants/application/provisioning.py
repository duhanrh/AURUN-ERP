"""Provisionamiento automático de tenants (sección 5.7).

Transacción **atómica**: crea el tenant, su branding por defecto, siembra los
roles base con sus permisos, activa el contexto RLS del nuevo tenant y crea el
usuario administrador inicial. Si cualquier paso falla, se revierte todo.

Idempotencia: el ``subdomain`` es la clave natural; reintentar con un subdominio
ya existente devuelve 409. (La clave de idempotencia explícita por petición y el
envío de credenciales por correo se incorporan en fases posteriores; aquí la
contraseña inicial se devuelve para que el operador la entregue.)

El catálogo de permisos de plataforma se asegura (upsert idempotente) dentro de la
misma transacción, de modo que el provisionamiento es autosuficiente.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.domain.chart import BASE_ACCOUNTS
from aurum.modules.accounting.infrastructure.models import ChartAccount
from aurum.modules.config.domain.currencies import BASE_CURRENCIES
from aurum.modules.config.domain.settings import DEFAULT_PARAMETERS, TOGGLEABLE_MODULES
from aurum.modules.config.domain.units import BASE_UNITS
from aurum.modules.config.infrastructure.models import (
    Currency,
    TenantBusinessParameters,
    TenantCompany,
    TenantModuleConfig,
    UnitOfMeasure,
)
from aurum.modules.inventory.domain.catalog import BASE_MATERIALS
from aurum.modules.inventory.infrastructure.models import Material
from aurum.modules.tenants.infrastructure.models import Tenant, TenantBranding
from aurum.modules.users.application.role_sync import (
    ensure_permission_catalog,
    sync_tenant_roles,
)
from aurum.modules.users.infrastructure.models import User
from aurum.shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class NewTenant:
    name: str
    subdomain: str
    admin_email: str
    admin_full_name: str
    subscription_plan: str = "free"
    admin_password: str | None = None


@dataclass(frozen=True, slots=True)
class ProvisionedTenant:
    tenant_id: uuid.UUID
    subdomain: str
    admin_email: str
    admin_user_id: uuid.UUID
    initial_password: str
    roles_created: int


class ProvisioningService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        password_hasher: Callable[[str], str],
    ) -> None:
        self._session = session
        self._hash = password_hasher

    async def provision(self, data: NewTenant) -> ProvisionedTenant:
        await self._guard_unique_subdomain(data.subdomain)
        catalog = await ensure_permission_catalog(self._session)

        tenant = Tenant(
            name=data.name,
            subdomain=data.subdomain,
            subscription_plan=data.subscription_plan,
            is_active=True,
        )
        self._session.add(tenant)
        await self._session.flush()  # materializa tenant.id

        # A partir de aquí escribimos filas con RLS: fijamos el tenant de la
        # transacción para satisfacer las políticas WITH CHECK (sección 5.5).
        await self._set_tenant_scope(tenant.id)

        self._session.add(TenantBranding(tenant_id=tenant.id, is_customized=False))
        self._seed_materials(tenant.id)
        self._seed_accounts(tenant.id)
        self._seed_configuration(tenant.id)
        self._seed_units(tenant.id)
        self._seed_currencies(tenant.id)
        self._session.add(TenantCompany(tenant_id=tenant.id))

        roles_by_slug = await sync_tenant_roles(self._session, tenant.id, catalog)
        admin_role = roles_by_slug["superusuario"]

        password = data.admin_password or secrets.token_urlsafe(12)
        admin = User(
            tenant_id=tenant.id,
            email=data.admin_email,
            full_name=data.admin_full_name,
            hashed_password=self._hash(password),
            role=admin_role,  # vía relación: el FK se fija al hacer flush
            is_active=True,
        )
        self._session.add(admin)
        await self._session.flush()

        return ProvisionedTenant(
            tenant_id=tenant.id,
            subdomain=tenant.subdomain,
            admin_email=admin.email,
            admin_user_id=admin.id,
            initial_password=password,
            roles_created=len(roles_by_slug),
        )

    async def _guard_unique_subdomain(self, subdomain: str) -> None:
        existing = await self._session.execute(
            select(Tenant.id).where(Tenant.subdomain == subdomain)
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"El subdominio '{subdomain}' ya está en uso.")

    async def _set_tenant_scope(self, tenant_id: uuid.UUID) -> None:
        await self._session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )

    def _seed_materials(self, tenant_id: uuid.UUID) -> None:
        """Siembra el catálogo base de materiales del tenant (sección 9)."""
        for definition in BASE_MATERIALS:
            self._session.add(
                Material(
                    tenant_id=tenant_id,
                    code=definition.code,
                    name=definition.name,
                    symbol=definition.symbol,
                    is_active=True,
                )
            )

    def _seed_units(self, tenant_id: uuid.UUID) -> None:
        """Siembra el catálogo base de unidades de medida del tenant (sección 7.17)."""
        for definition in BASE_UNITS:
            self._session.add(
                UnitOfMeasure(
                    tenant_id=tenant_id,
                    code=definition.code,
                    name=definition.name,
                    symbol=definition.symbol,
                    grams_factor=definition.grams_factor,
                    is_base=definition.is_base,
                    is_active=True,
                )
            )

    def _seed_currencies(self, tenant_id: uuid.UUID) -> None:
        """Siembra el catálogo base de monedas; la base = parámetro ``base_currency``."""
        base_code = DEFAULT_PARAMETERS.base_currency
        for definition in BASE_CURRENCIES:
            self._session.add(
                Currency(
                    tenant_id=tenant_id,
                    code=definition.code,
                    name=definition.name,
                    symbol=definition.symbol,
                    decimals=definition.decimals,
                    is_base=definition.code == base_code,
                    is_active=True,
                )
            )

    def _seed_accounts(self, tenant_id: uuid.UUID) -> None:
        """Siembra el plan de cuentas base del tenant (sección 7.12)."""
        for definition in BASE_ACCOUNTS:
            self._session.add(
                ChartAccount(
                    tenant_id=tenant_id,
                    code=definition.code,
                    name=definition.name,
                    type=definition.type,
                    normal_balance=definition.normal_balance,
                    is_active=True,
                )
            )

    def _seed_configuration(self, tenant_id: uuid.UUID) -> None:
        """Siembra parámetros de negocio por defecto y módulos activos (sección 7.17)."""
        d = DEFAULT_PARAMETERS
        self._session.add(
            TenantBusinessParameters(
                tenant_id=tenant_id,
                base_currency=d.base_currency,
                weight_unit=d.weight_unit,
                min_stock_g=d.min_stock_g,
                min_margin_pct=d.min_margin_pct,
                language=d.language,
                timezone=d.timezone,
                date_format=d.date_format,
                regulatory_entity=d.regulatory_entity,
            )
        )
        for module in TOGGLEABLE_MODULES:
            self._session.add(
                TenantModuleConfig(tenant_id=tenant_id, module_key=module.key, is_active=True)
            )
