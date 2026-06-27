"""Caso de uso del Dashboard: agrega KPIs, alertas y stock de todos los módulos.

Es una **proyección de lectura** (sección 7.16): no introduce entidades propias;
calcula sobre datos reales de Inventario, Ventas, Compras, Calidad y Contabilidad.
Las alertas se derivan de reglas de negocio (stock crítico vs parámetro del tenant,
OC pendientes, muestras de lab pendientes, cartera por cobrar), no hardcodeadas.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from aurum.modules.accounting.application.services import AccountingService
from aurum.modules.config.application.ports import ParametersRepository
from aurum.modules.config.domain.settings import DEFAULT_PARAMETERS
from aurum.modules.dashboard.application.dto import (
    Alert,
    DashboardKpis,
    DashboardSummary,
    MaterialStock,
    RecentTransaction,
    SpotPriceView,
)
from aurum.modules.dashboard.domain.spot import get_spot_prices
from aurum.modules.inventory.application.ports import LotRepository, MaterialRepository
from aurum.modules.inventory.domain.valuation import valuation_usd
from aurum.modules.purchasing.application.ports import PurchaseOrderRepository
from aurum.modules.quality.application.ports import QualitySampleRepository
from aurum.modules.sales.application.ports import SalesOrderRepository

CENTS = Decimal("0.01")
_RECENT_LIMIT = 8


class DashboardService:
    def __init__(
        self,
        *,
        lots: LotRepository,
        materials: MaterialRepository,
        sales: SalesOrderRepository,
        purchases: PurchaseOrderRepository,
        samples: QualitySampleRepository,
        accounting: AccountingService,
        parameters: ParametersRepository,
    ) -> None:
        self._lots = lots
        self._materials = materials
        self._sales = sales
        self._purchases = purchases
        self._samples = samples
        self._accounting = accounting
        self._parameters = parameters

    async def summary(self) -> DashboardSummary:
        lots = await self._lots.list_all()
        materials = await self._materials.list_active()
        sales = await self._sales.list_all()
        purchases = await self._purchases.list_all()
        samples = await self._samples.list_all()
        acc = await self._accounting.kpis()
        params = await self._parameters.get()
        min_stock = params.min_stock_g if params is not None else DEFAULT_PARAMETERS.min_stock_g

        # ── Inventario por material ──
        weight_by_material: dict[object, Decimal] = defaultdict(lambda: Decimal("0"))
        value_by_material: dict[object, Decimal] = defaultdict(lambda: Decimal("0"))
        for lot in lots:
            weight_by_material[lot.material_id] += lot.available_weight_g
            value_by_material[lot.material_id] += valuation_usd(
                lot.available_weight_g, lot.declared_purity, lot.price_per_oz
            )

        material_stock: list[MaterialStock] = []
        for m in materials:
            weight = weight_by_material.get(m.id, Decimal("0"))
            is_critical = Decimal("0") < weight < min_stock
            material_stock.append(
                MaterialStock(
                    code=m.code,
                    name=m.name,
                    symbol=m.symbol,
                    available_weight_g=weight.quantize(Decimal("0.0001")),
                    value_usd=value_by_material.get(m.id, Decimal("0")).quantize(CENTS),
                    is_critical=is_critical,
                )
            )

        inventory_value = sum(value_by_material.values(), Decimal("0")).quantize(CENTS)
        inventory_weight = sum(weight_by_material.values(), Decimal("0")).quantize(
            Decimal("0.0001")
        )

        # ── Ventas / Compras ──
        sales_total = Decimal("0")
        for o in sales:
            if o.status == "cancelled":
                continue
            purity = o.lot.declared_purity if o.lot else Decimal("0")
            sales_total += valuation_usd(o.quantity_g, purity, o.price_per_oz)
        purchases_pending = sum(1 for o in purchases if o.status == "pending_approval")

        kpis = DashboardKpis(
            inventory_value_usd=inventory_value,
            inventory_weight_g=inventory_weight,
            total_lots=len(lots),
            sales_total_usd=sales_total.quantize(CENTS),
            sales_count=len(sales),
            purchases_pending=purchases_pending,
            net_income_usd=acc.net_income,
            cash_balance_usd=acc.cash_balance,
            receivable_usd=acc.receivable_total,
            payable_usd=acc.payable_total,
        )

        # ── Alertas (reglas de negocio) ──
        alerts: list[Alert] = []
        for ms in material_stock:
            if ms.is_critical:
                alerts.append(
                    Alert(
                        level="critical",
                        category="stock",
                        message=(
                            f"Stock bajo de {ms.name}: {ms.available_weight_g} g "
                            f"(mínimo {min_stock} g)."
                        ),
                    )
                )
        if purchases_pending:
            alerts.append(
                Alert(
                    level="warning",
                    category="purchasing",
                    message=f"{purchases_pending} orden(es) de compra pendiente(s) de aprobación.",
                )
            )
        pending_samples = sum(1 for s in samples if s.result == "pending")
        if pending_samples:
            alerts.append(
                Alert(
                    level="info",
                    category="quality",
                    message=f"{pending_samples} muestra(s) de laboratorio pendiente(s).",
                )
            )
        if acc.receivable_total > 0:
            alerts.append(
                Alert(
                    level="info",
                    category="accounting",
                    message=f"Cuentas por cobrar pendientes: ${acc.receivable_total}.",
                )
            )

        # ── Transacciones recientes (ventas + compras) ──
        transactions: list[RecentTransaction] = []
        for o in sales:
            purity = o.lot.declared_purity if o.lot else Decimal("0")
            transactions.append(
                RecentTransaction(
                    kind="sale",
                    code=o.order_code,
                    party_name=o.customer.legal_name if o.customer else "—",
                    amount_usd=valuation_usd(o.quantity_g, purity, o.price_per_oz).quantize(CENTS),
                    status=o.status,
                    created_at=o.created_at,
                )
            )
        for po in purchases:
            transactions.append(
                RecentTransaction(
                    kind="purchase",
                    code=po.order_code,
                    party_name=po.supplier.legal_name if po.supplier else "—",
                    amount_usd=valuation_usd(
                        po.quantity_g, po.declared_purity, po.price_per_oz
                    ).quantize(CENTS),
                    status=po.status,
                    created_at=po.created_at,
                )
            )
        transactions.sort(key=lambda t: t.created_at or datetime.min, reverse=True)

        spot = [
            SpotPriceView(
                symbol=p.symbol,
                name=p.name,
                price_usd_per_oz=p.price_usd_per_oz,
                change_pct=p.change_pct,
                stale=p.stale,
            )
            for p in get_spot_prices()
        ]

        return DashboardSummary(
            kpis=kpis,
            alerts=alerts,
            material_stock=material_stock,
            recent_transactions=transactions[:_RECENT_LIMIT],
            spot_prices=spot,
            min_stock_g=min_stock,
        )
