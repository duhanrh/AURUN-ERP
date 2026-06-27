"""DTOs del Dashboard (agregación de solo lectura de todos los módulos)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DashboardKpis:
    inventory_value_usd: Decimal
    inventory_weight_g: Decimal
    total_lots: int
    sales_total_usd: Decimal
    sales_count: int
    purchases_pending: int
    net_income_usd: Decimal
    cash_balance_usd: Decimal
    receivable_usd: Decimal
    payable_usd: Decimal


@dataclass(frozen=True, slots=True)
class Alert:
    level: str  # critical | warning | info
    category: str
    message: str


@dataclass(frozen=True, slots=True)
class MaterialStock:
    code: str
    name: str
    symbol: str
    available_weight_g: Decimal
    value_usd: Decimal
    is_critical: bool


@dataclass(frozen=True, slots=True)
class RecentTransaction:
    kind: str  # sale | purchase
    code: str
    party_name: str
    amount_usd: Decimal
    status: str
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class SpotPriceView:
    symbol: str
    name: str
    price_usd_per_oz: Decimal
    change_pct: Decimal
    stale: bool


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    kpis: DashboardKpis
    alerts: list[Alert]
    material_stock: list[MaterialStock]
    recent_transactions: list[RecentTransaction]
    spot_prices: list[SpotPriceView]
    min_stock_g: Decimal
