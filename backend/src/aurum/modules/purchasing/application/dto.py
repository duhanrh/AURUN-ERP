"""DTOs del módulo de Compras."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from aurum.modules.inventory.domain.valuation import LotForm
from aurum.modules.purchasing.domain.order import PurchaseOrderStatus


@dataclass(frozen=True, slots=True)
class PurchaseOrderView:
    id: uuid.UUID
    order_code: str
    supplier_id: uuid.UUID
    supplier_name: str
    material_id: uuid.UUID
    material_name: str
    quantity_g: Decimal
    declared_purity: Decimal
    form: LotForm
    price_per_oz: Decimal
    total_usd: Decimal
    location: str | None
    expected_delivery: date | None
    status: PurchaseOrderStatus
    lot_id: uuid.UUID | None
    created_at: datetime | None
    is_deleted: bool = False


@dataclass(frozen=True, slots=True)
class PurchaseOrderPatch:
    """Cambios de una OC; sólo editable mientras esté ``pending_approval``."""

    quantity_g: Decimal | None = None
    declared_purity: Decimal | None = None
    price_per_oz: Decimal | None = None
    form: LotForm | None = None
    location: str | None = None
    expected_delivery: date | None = None
    notes: str | None = None
    fields_set: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class PurchasingKpis:
    total_orders: int
    pending_approval: int
    approved: int
    total_amount_usd: Decimal


@dataclass(frozen=True, slots=True)
class NewPurchaseOrder:
    """Alta de OC (modal-compra): proveedor, material, cantidad, precio, entrega."""

    supplier_id: uuid.UUID
    material_id: uuid.UUID
    quantity_g: Decimal
    declared_purity: Decimal
    price_per_oz: Decimal
    form: LotForm = "raw"
    location: str | None = None
    expected_delivery: date | None = None
    notes: str | None = None
