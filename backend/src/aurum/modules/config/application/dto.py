"""DTOs del módulo de Configuración."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BrandingView:
    brand_name: str | None
    tagline: str | None
    logo_url: str | None
    color_primary: str | None
    color_background: str | None
    color_success: str | None
    color_danger: str | None
    is_customized: bool


@dataclass(frozen=True, slots=True)
class BrandingUpdate:
    brand_name: str | None
    tagline: str | None
    logo_url: str | None
    color_primary: str | None
    color_background: str | None
    color_success: str | None
    color_danger: str | None


@dataclass(frozen=True, slots=True)
class ParametersView:
    base_currency: str
    weight_unit: str
    min_stock_g: Decimal
    min_margin_pct: Decimal
    language: str
    timezone: str
    date_format: str
    regulatory_entity: str


@dataclass(frozen=True, slots=True)
class ParametersUpdate:
    base_currency: str
    weight_unit: str
    min_stock_g: Decimal
    min_margin_pct: Decimal
    language: str
    timezone: str
    date_format: str
    regulatory_entity: str


@dataclass(frozen=True, slots=True)
class ModuleView:
    key: str
    label: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class UnitView:
    id: str
    code: str
    name: str
    symbol: str
    grams_factor: Decimal
    is_base: bool
    is_active: bool
    is_deleted: bool


@dataclass(frozen=True, slots=True)
class UnitCreate:
    code: str
    name: str
    symbol: str
    grams_factor: Decimal
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UnitPatch:
    name: str | None = None
    symbol: str | None = None
    grams_factor: Decimal | None = None
    is_active: bool | None = None
