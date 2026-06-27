"""Casos de uso de Configuración: marca, parámetros y módulos por tenant (7.17).

La marca personalizada persiste en ``tenant_branding`` (no en ``localStorage``):
al guardar cualquier color/identidad, ``is_customized`` pasa a ``true``; un tenant
sin personalizar conserva ``is_customized=false`` y el frontend aplica el tema
"Aurum" por defecto (sección 5.6, criterio de aceptación de la Fase 7).
"""

from __future__ import annotations

from aurum.modules.config.application.dto import (
    BrandingUpdate,
    BrandingView,
    ModuleView,
    ParametersUpdate,
    ParametersView,
)
from aurum.modules.config.application.ports import (
    BrandingRepository,
    ModuleConfigRepository,
    ParametersRepository,
)
from aurum.modules.config.domain.settings import TOGGLEABLE_MODULES
from aurum.modules.config.infrastructure.models import TenantBusinessParameters
from aurum.modules.tenants.infrastructure.models import TenantBranding
from aurum.shared.errors import NotFoundError


class ConfigService:
    def __init__(
        self,
        *,
        branding: BrandingRepository,
        parameters: ParametersRepository,
        modules: ModuleConfigRepository,
    ) -> None:
        self._branding = branding
        self._parameters = parameters
        self._modules = modules

    # ── Marca ──────────────────────────────────────────────────────────────
    async def get_branding(self) -> BrandingView:
        branding = await self._branding.get()
        if branding is None:
            raise NotFoundError("El tenant no tiene branding inicializado.")
        return _branding_to_view(branding)

    async def update_branding(self, data: BrandingUpdate) -> BrandingView:
        branding = await self._branding.get()
        if branding is None:
            raise NotFoundError("El tenant no tiene branding inicializado.")
        branding.brand_name = data.brand_name
        branding.tagline = data.tagline
        branding.logo_url = data.logo_url
        branding.color_primary = data.color_primary
        branding.color_background = data.color_background
        branding.color_success = data.color_success
        branding.color_danger = data.color_danger
        branding.is_customized = True  # cualquier guardado marca personalización
        return _branding_to_view(branding)

    async def reset_branding(self) -> BrandingView:
        branding = await self._branding.get()
        if branding is None:
            raise NotFoundError("El tenant no tiene branding inicializado.")
        branding.brand_name = None
        branding.tagline = None
        branding.logo_url = None
        branding.color_primary = None
        branding.color_background = None
        branding.color_success = None
        branding.color_danger = None
        branding.is_customized = False
        return _branding_to_view(branding)

    # ── Parámetros de negocio ──────────────────────────────────────────────
    async def get_parameters(self) -> ParametersView:
        params = await self._require_params()
        return _params_to_view(params)

    async def update_parameters(self, data: ParametersUpdate) -> ParametersView:
        params = await self._require_params()
        params.base_currency = data.base_currency
        params.weight_unit = data.weight_unit
        params.min_stock_g = data.min_stock_g
        params.min_margin_pct = data.min_margin_pct
        params.language = data.language
        params.timezone = data.timezone
        params.date_format = data.date_format
        params.regulatory_entity = data.regulatory_entity
        return _params_to_view(params)

    # ── Módulos activos ────────────────────────────────────────────────────
    async def list_modules(self) -> list[ModuleView]:
        active = {m.module_key: m.is_active for m in await self._modules.list_all()}
        return [
            ModuleView(key=m.key, label=m.label, is_active=active.get(m.key, True))
            for m in TOGGLEABLE_MODULES
        ]

    async def set_module(self, module_key: str, is_active: bool) -> ModuleView:
        row = await self._modules.get(module_key)
        if row is None:
            raise NotFoundError(f"Módulo '{module_key}' no existe en la configuración.")
        row.is_active = is_active
        label = next((m.label for m in TOGGLEABLE_MODULES if m.key == module_key), module_key)
        return ModuleView(key=module_key, label=label, is_active=is_active)

    async def _require_params(self) -> TenantBusinessParameters:
        params = await self._parameters.get()
        if params is None:
            raise NotFoundError("El tenant no tiene parámetros inicializados.")
        return params


def _branding_to_view(b: TenantBranding) -> BrandingView:
    return BrandingView(
        brand_name=b.brand_name,
        tagline=b.tagline,
        logo_url=b.logo_url,
        color_primary=b.color_primary,
        color_background=b.color_background,
        color_success=b.color_success,
        color_danger=b.color_danger,
        is_customized=b.is_customized,
    )


def _params_to_view(p: TenantBusinessParameters) -> ParametersView:
    return ParametersView(
        base_currency=p.base_currency,
        weight_unit=p.weight_unit,
        min_stock_g=p.min_stock_g,
        min_margin_pct=p.min_margin_pct,
        language=p.language,
        timezone=p.timezone,
        date_format=p.date_format,
        regulatory_entity=p.regulatory_entity,
    )
