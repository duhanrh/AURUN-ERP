"""Esquemas Pydantic de la API de Inventario (sección 7.1)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.inventory.application.dto import (
    InventoryKpis,
    LotView,
    MaterialView,
    NewLot,
)
from aurum.modules.inventory.domain.valuation import LotForm, LotStatus


class MaterialResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    symbol: str
    is_active: bool

    @classmethod
    def from_view(cls, v: MaterialView) -> MaterialResponse:
        return cls(id=v.id, code=v.code, name=v.name, symbol=v.symbol, is_active=v.is_active)


class LotResponse(BaseModel):
    id: uuid.UUID
    lot_code: str
    material_id: uuid.UUID
    material_code: str
    material_name: str
    form: str
    declared_purity: Decimal
    gross_weight_g: Decimal
    available_weight_g: Decimal
    net_weight_g: Decimal
    price_per_oz: Decimal
    value_usd: Decimal
    status: str
    location: str | None
    supplier_id: uuid.UUID | None
    entry_date: date | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, v: LotView) -> LotResponse:
        return cls(
            id=v.id,
            lot_code=v.lot_code,
            material_id=v.material_id,
            material_code=v.material_code,
            material_name=v.material_name,
            form=v.form,
            declared_purity=v.declared_purity,
            gross_weight_g=v.gross_weight_g,
            available_weight_g=v.available_weight_g,
            net_weight_g=v.net_weight_g,
            price_per_oz=v.price_per_oz,
            value_usd=v.value_usd,
            status=v.status,
            location=v.location,
            supplier_id=v.supplier_id,
            entry_date=v.entry_date,
            created_at=v.created_at,
        )


class InventoryKpisResponse(BaseModel):
    total_lots: int
    total_gross_weight_g: Decimal
    total_value_usd: Decimal
    raw_lots: int
    refined_lots: int

    @classmethod
    def from_view(cls, v: InventoryKpis) -> InventoryKpisResponse:
        return cls(
            total_lots=v.total_lots,
            total_gross_weight_g=v.total_gross_weight_g,
            total_value_usd=v.total_value_usd,
            raw_lots=v.raw_lots,
            refined_lots=v.refined_lots,
        )


class CreateLotRequest(BaseModel):
    material_id: uuid.UUID
    form: LotForm = "raw"
    declared_purity: Decimal = Field(gt=0, le=1)
    gross_weight_g: Decimal = Field(gt=0)
    price_per_oz: Decimal = Field(gt=0)
    location: str | None = Field(default=None, max_length=120)
    supplier_id: uuid.UUID | None = None
    status: LotStatus = "available"
    entry_date: date | None = None

    def to_new_lot(self) -> NewLot:
        return NewLot(
            material_id=self.material_id,
            form=self.form,
            declared_purity=self.declared_purity,
            gross_weight_g=self.gross_weight_g,
            price_per_oz=self.price_per_oz,
            location=self.location,
            supplier_id=self.supplier_id,
            status=self.status,
            entry_date=self.entry_date,
        )
