"""DTOs del módulo de Inventario (independientes del ORM y de la API)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from aurum.modules.inventory.domain.valuation import LotForm, LotStatus


@dataclass(frozen=True, slots=True)
class MaterialView:
    id: uuid.UUID
    code: str
    name: str
    symbol: str
    is_active: bool
    is_deleted: bool = False


@dataclass(frozen=True, slots=True)
class NewMaterial:
    code: str
    name: str
    symbol: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class MaterialPatch:
    name: str | None = None
    symbol: str | None = None
    is_active: bool | None = None
    fields_set: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class LotView:
    id: uuid.UUID
    lot_code: str
    material_id: uuid.UUID
    material_code: str
    material_name: str
    form: LotForm
    declared_purity: Decimal
    gross_weight_g: Decimal
    available_weight_g: Decimal
    net_weight_g: Decimal
    price_per_oz: Decimal
    value_usd: Decimal
    status: LotStatus
    location: str | None
    supplier_id: uuid.UUID | None
    entry_date: date | None
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class InventoryKpis:
    total_lots: int
    total_gross_weight_g: Decimal
    total_value_usd: Decimal
    raw_lots: int
    refined_lots: int


@dataclass(frozen=True, slots=True)
class NewLot:
    """Alta manual de lote (modal-lote): material, tipo, pureza, peso, ubicación."""

    material_id: uuid.UUID
    form: LotForm
    declared_purity: Decimal
    gross_weight_g: Decimal
    price_per_oz: Decimal
    location: str | None = None
    supplier_id: uuid.UUID | None = None
    status: LotStatus = "available"
    entry_date: date | None = None
    lot_code: str | None = None
