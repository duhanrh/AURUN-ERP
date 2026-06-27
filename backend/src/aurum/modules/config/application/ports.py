"""Puertos (Protocols) del módulo de Configuración."""

from __future__ import annotations

from typing import Protocol

from aurum.modules.config.infrastructure.models import (
    TenantBusinessParameters,
    TenantModuleConfig,
)
from aurum.modules.tenants.infrastructure.models import TenantBranding


class BrandingRepository(Protocol):
    async def get(self) -> TenantBranding | None: ...


class ParametersRepository(Protocol):
    async def get(self) -> TenantBusinessParameters | None: ...


class ModuleConfigRepository(Protocol):
    async def list_all(self) -> list[TenantModuleConfig]: ...
    async def get(self, module_key: str) -> TenantModuleConfig | None: ...
