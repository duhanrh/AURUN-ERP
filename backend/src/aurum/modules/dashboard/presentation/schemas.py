"""Esquemas Pydantic de la API del Dashboard (sección 7.16)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from aurum.modules.dashboard.application.dto import DashboardSummary


class DashboardKpisResponse(BaseModel):
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


class AlertResponse(BaseModel):
    level: str
    category: str
    message: str


class MaterialStockResponse(BaseModel):
    code: str
    name: str
    symbol: str
    available_weight_g: Decimal
    value_usd: Decimal
    is_critical: bool


class RecentTransactionResponse(BaseModel):
    kind: str
    code: str
    party_name: str
    amount_usd: Decimal
    status: str
    created_at: datetime | None


class SpotPriceResponse(BaseModel):
    symbol: str
    name: str
    price_usd_per_oz: Decimal
    change_pct: Decimal
    stale: bool


class DashboardSummaryResponse(BaseModel):
    kpis: DashboardKpisResponse
    alerts: list[AlertResponse]
    material_stock: list[MaterialStockResponse]
    recent_transactions: list[RecentTransactionResponse]
    spot_prices: list[SpotPriceResponse]
    min_stock_g: Decimal

    @classmethod
    def from_view(cls, v: DashboardSummary) -> DashboardSummaryResponse:
        return cls(
            kpis=DashboardKpisResponse(
                inventory_value_usd=v.kpis.inventory_value_usd,
                inventory_weight_g=v.kpis.inventory_weight_g,
                total_lots=v.kpis.total_lots,
                sales_total_usd=v.kpis.sales_total_usd,
                sales_count=v.kpis.sales_count,
                purchases_pending=v.kpis.purchases_pending,
                net_income_usd=v.kpis.net_income_usd,
                cash_balance_usd=v.kpis.cash_balance_usd,
                receivable_usd=v.kpis.receivable_usd,
                payable_usd=v.kpis.payable_usd,
            ),
            alerts=[
                AlertResponse(level=a.level, category=a.category, message=a.message)
                for a in v.alerts
            ],
            material_stock=[
                MaterialStockResponse(
                    code=m.code,
                    name=m.name,
                    symbol=m.symbol,
                    available_weight_g=m.available_weight_g,
                    value_usd=m.value_usd,
                    is_critical=m.is_critical,
                )
                for m in v.material_stock
            ],
            recent_transactions=[
                RecentTransactionResponse(
                    kind=t.kind,
                    code=t.code,
                    party_name=t.party_name,
                    amount_usd=t.amount_usd,
                    status=t.status,
                    created_at=t.created_at,
                )
                for t in v.recent_transactions
            ],
            spot_prices=[
                SpotPriceResponse(
                    symbol=s.symbol,
                    name=s.name,
                    price_usd_per_oz=s.price_usd_per_oz,
                    change_pct=s.change_pct,
                    stale=s.stale,
                )
                for s in v.spot_prices
            ],
            min_stock_g=v.min_stock_g,
        )
