"""Puertos (Protocols) del módulo de Configuración."""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.config.infrastructure.models import (
    TenantBusinessParameters,
    TenantModuleConfig,
    UnitOfMeasure,
)
from aurum.modules.tenants.infrastructure.models import TenantBranding


class BrandingRepository(Protocol):
    async def get(self) -> TenantBranding | None: ...


class ParametersRepository(Protocol):
    async def get(self) -> TenantBusinessParameters | None: ...


class ModuleConfigRepository(Protocol):
    async def list_all(self) -> list[TenantModuleConfig]: ...
    async def get(self, module_key: str) -> TenantModuleConfig | None: ...


class UnitOfMeasureRepository(Protocol):
    async def list_all(self, *, include_deleted: bool = False) -> list[UnitOfMeasure]: ...
    async def get(self, unit_id: uuid.UUID) -> UnitOfMeasure | None: ...
    async def get_by_code(self, code: str) -> UnitOfMeasure | None: ...
    async def add(self, unit: UnitOfMeasure) -> UnitOfMeasure: ...
