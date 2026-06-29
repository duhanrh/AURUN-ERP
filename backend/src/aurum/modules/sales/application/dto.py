"""DTOs del módulo de Ventas."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from aurum.modules.sales.domain.order import SalesOrderStatus


@dataclass(frozen=True, slots=True)
class SalesOrderView:
    id: uuid.UUID
    order_code: str
    customer_id: uuid.UUID
    customer_name: str
    lot_id: uuid.UUID
    lot_code: str
    material_name: str
    declared_purity: Decimal
    quantity_g: Decimal
    price_per_oz: Decimal
    total_usd: Decimal
    status: SalesOrderStatus
    invoice_number: str | None
    created_at: datetime | None
    is_deleted: bool = False


@dataclass(frozen=True, slots=True)
class SalesOrderPatch:
    """Cambios de una OV; sólo editable mientras esté ``pending_payment``."""

    price_per_oz: Decimal | None = None
    invoice_number: str | None = None
    fields_set: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class SalesKpis:
    total_orders: int
    pending_payment: int
    completed: int
    total_amount_usd: Decimal


@dataclass(frozen=True, slots=True)
class NewSalesOrder:
    """Alta de OV (modal-venta): cliente, lote a vender, cantidad, precio."""

    customer_id: uuid.UUID
    lot_id: uuid.UUID
    quantity_g: Decimal
    price_per_oz: Decimal
    invoice_number: str | None = None
