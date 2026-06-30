"""Esquemas Pydantic de la API de Configuración (sección 7.17)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.config.application.dto import (
    BrandingUpdate,
    BrandingView,
    ModuleView,
    ParametersUpdate,
    ParametersView,
    UnitCreate,
    UnitPatch,
    UnitView,
)

_HEX = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"


class BrandingResponse(BaseModel):
    brand_name: str | None
    tagline: str | None
    logo_url: str | None
    color_primary: str | None
    color_background: str | None
    color_success: str | None
    color_danger: str | None
    is_customized: bool

    @classmethod
    def from_view(cls, v: BrandingView) -> BrandingResponse:
        return cls(
            brand_name=v.brand_name,
            tagline=v.tagline,
            logo_url=v.logo_url,
            color_primary=v.color_primary,
            color_background=v.color_background,
            color_success=v.color_success,
            color_danger=v.color_danger,
            is_customized=v.is_customized,
        )


class UpdateBrandingRequest(BaseModel):
    brand_name: str | None = Field(default=None, max_length=160)
    tagline: str | None = Field(default=None, max_length=160)
    logo_url: str | None = Field(default=None, max_length=512)
    color_primary: str | None = Field(default=None, pattern=_HEX)
    color_background: str | None = Field(default=None, pattern=_HEX)
    color_success: str | None = Field(default=None, pattern=_HEX)
    color_danger: str | None = Field(default=None, pattern=_HEX)

    def to_dto(self) -> BrandingUpdate:
        return BrandingUpdate(
            brand_name=self.brand_name,
            tagline=self.tagline,
            logo_url=self.logo_url,
            color_primary=self.color_primary,
            color_background=self.color_background,
            color_success=self.color_success,
            color_danger=self.color_danger,
        )


class ParametersResponse(BaseModel):
    base_currency: str
    weight_unit: str
    min_stock_g: Decimal
    min_margin_pct: Decimal
    language: str
    timezone: str
    date_format: str
    regulatory_entity: str

    @classmethod
    def from_view(cls, v: ParametersView) -> ParametersResponse:
        return cls(
            base_currency=v.base_currency,
            weight_unit=v.weight_unit,
            min_stock_g=v.min_stock_g,
            min_margin_pct=v.min_margin_pct,
            language=v.language,
            timezone=v.timezone,
            date_format=v.date_format,
            regulatory_entity=v.regulatory_entity,
        )


class UpdateParametersRequest(BaseModel):
    base_currency: str = Field(max_length=8)
    weight_unit: str = Field(max_length=4)
    min_stock_g: Decimal = Field(ge=0)
    min_margin_pct: Decimal = Field(ge=0, le=100)
    language: str = Field(max_length=8)
    timezone: str = Field(max_length=48)
    date_format: str = Field(max_length=16)
    regulatory_entity: str = Field(default="", max_length=120)

    def to_dto(self) -> ParametersUpdate:
        return ParametersUpdate(
            base_currency=self.base_currency,
            weight_unit=self.weight_unit,
            min_stock_g=self.min_stock_g,
            min_margin_pct=self.min_margin_pct,
            language=self.language,
            timezone=self.timezone,
            date_format=self.date_format,
            regulatory_entity=self.regulatory_entity,
        )


class ModuleResponse(BaseModel):
    key: str
    label: str
    is_active: bool

    @classmethod
    def from_view(cls, v: ModuleView) -> ModuleResponse:
        return cls(key=v.key, label=v.label, is_active=v.is_active)


class SetModuleRequest(BaseModel):
    is_active: bool


class UnitResponse(BaseModel):
    id: str
    code: str
    name: str
    symbol: str
    grams_factor: Decimal
    is_base: bool
    is_active: bool
    is_deleted: bool

    @classmethod
    def from_view(cls, v: UnitView) -> UnitResponse:
        return cls(
            id=v.id,
            code=v.code,
            name=v.name,
            symbol=v.symbol,
            grams_factor=v.grams_factor,
            is_base=v.is_base,
            is_active=v.is_active,
            is_deleted=v.is_deleted,
        )


class CreateUnitRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    symbol: str = Field(min_length=1, max_length=8)
    grams_factor: Decimal = Field(gt=0)
    is_active: bool = True

    def to_dto(self) -> UnitCreate:
        return UnitCreate(
            code=self.code,
            name=self.name,
            symbol=self.symbol,
            grams_factor=self.grams_factor,
            is_active=self.is_active,
        )


class UpdateUnitRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    symbol: str | None = Field(default=None, min_length=1, max_length=8)
    grams_factor: Decimal | None = Field(default=None, gt=0)
    is_active: bool | None = None

    def to_patch(self) -> UnitPatch:
        return UnitPatch(
            name=self.name,
            symbol=self.symbol,
            grams_factor=self.grams_factor,
            is_active=self.is_active,
        )


class ConvertRequest(BaseModel):
    quantity: Decimal = Field(ge=0)
    from_unit: str = Field(min_length=1, max_length=32)
    to_unit: str = Field(min_length=1, max_length=32)


class ConvertResponse(BaseModel):
    quantity: Decimal
    from_unit: str
    to_unit: str
    grams: Decimal
    result: Decimal
