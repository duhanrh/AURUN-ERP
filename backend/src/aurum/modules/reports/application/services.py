"""Casos de uso de Reportes (sección 7.15): genera los 6 reportes con datos reales.

Cada reporte arma una ``ReportTable`` con cabecera de marca (nombre del tenant +
número de documento + fecha) y filas calculadas en vivo desde los módulos. No hay
datos simulados: todo proviene del tenant autenticado (RLS lo acota).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from aurum.modules.accounting.application.services import AccountingService
from aurum.modules.config.application.ports import BrandingRepository, ParametersRepository
from aurum.modules.dashboard.domain.spot import get_spot_prices
from aurum.modules.inventory.application.ports import LotRepository, MaterialRepository
from aurum.modules.inventory.domain.valuation import fine_weight_g, valuation_usd
from aurum.modules.purchasing.application.ports import PurchaseOrderRepository
from aurum.modules.quality.application.ports import QualitySampleRepository
from aurum.modules.reports.application.dto import ReportTable, ReportTypeView, SummaryItem
from aurum.modules.reports.domain.catalog import REPORT_BY_KEY, REPORT_CATALOG
from aurum.modules.sales.application.ports import SalesOrderRepository
from aurum.modules.transformation.application.ports import TransformationOrderRepository
from aurum.shared.codes import generate_code
from aurum.shared.errors import NotFoundError

ZERO = Decimal("0")


def _money(value: Decimal) -> str:
    return f"${value:,.2f}"


def _grams(value: Decimal) -> str:
    return f"{value:,.4f} g"


def _pct(value: Decimal) -> str:
    return f"{value:.2f}%"


class ReportsService:
    def __init__(
        self,
        *,
        lots: LotRepository,
        materials: MaterialRepository,
        sales: SalesOrderRepository,
        purchases: PurchaseOrderRepository,
        transformations: TransformationOrderRepository,
        samples: QualitySampleRepository,
        accounting: AccountingService,
        branding: BrandingRepository,
        parameters: ParametersRepository,
    ) -> None:
        self._lots = lots
        self._materials = materials
        self._sales = sales
        self._purchases = purchases
        self._transformations = transformations
        self._samples = samples
        self._accounting = accounting
        self._branding = branding
        self._parameters = parameters

    def list_types(self) -> list[ReportTypeView]:
        return [
            ReportTypeView(key=r.key, title=r.title, description=r.description)
            for r in REPORT_CATALOG
        ]

    async def generate(self, key: str) -> ReportTable:
        definition = REPORT_BY_KEY.get(key)
        if definition is None:
            raise NotFoundError(f"Reporte '{key}' no existe.")
        builder = {
            "inventory_valued": self._inventory_valued,
            "profit_loss": self._profit_loss,
            "lot_traceability": self._lot_traceability,
            "regulatory": self._regulatory,
            "operational_kpis": self._operational_kpis,
            "price_analysis": self._price_analysis,
        }[key]
        columns, rows, summary = await builder()
        return ReportTable(
            key=key,
            title=definition.title,
            brand_name=await self._brand_name(),
            document_number=generate_code("REP"),
            generated_at=datetime.now(),
            columns=columns,
            rows=rows,
            summary=summary,
        )

    async def _brand_name(self) -> str:
        branding = await self._branding.get()
        if branding is not None and branding.brand_name:
            return branding.brand_name
        return "AURUM ERP"

    # ── Reportes ────────────────────────────────────────────────────────────
    async def _inventory_valued(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        lots = await self._lots.list_all()
        columns = ["Lote", "Material", "Forma", "Peso disp.", "Pureza", "Precio/oz", "Valor"]
        rows: list[list[str]] = []
        total_value = ZERO
        total_weight = ZERO
        for lot in lots:
            value = valuation_usd(lot.available_weight_g, lot.declared_purity, lot.price_per_oz)
            total_value += value
            total_weight += lot.available_weight_g
            rows.append(
                [
                    lot.lot_code,
                    lot.material.name if lot.material else "—",
                    lot.form,
                    _grams(lot.available_weight_g),
                    _pct(lot.declared_purity * 100),
                    _money(lot.price_per_oz),
                    _money(value),
                ]
            )
        summary = [
            SummaryItem("Lotes", str(len(lots))),
            SummaryItem("Peso disponible total", _grams(total_weight)),
            SummaryItem("Valor total", _money(total_value)),
        ]
        return columns, rows, summary

    async def _profit_loss(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        kpis = await self._accounting.kpis()
        columns = ["Concepto", "Valor USD"]
        rows = [
            ["Ingresos por venta", _money(kpis.total_income)],
            ["Costos y gastos", _money(kpis.total_expense)],
            ["Utilidad neta", _money(kpis.net_income)],
        ]
        margin = (
            (kpis.net_income / kpis.total_income * 100) if kpis.total_income > 0 else ZERO
        )
        summary = [
            SummaryItem("Utilidad neta", _money(kpis.net_income)),
            SummaryItem("Margen neto", _pct(margin)),
        ]
        return columns, rows, summary

    async def _lot_traceability(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        lots = await self._lots.list_all()
        columns = ["Lote", "Material", "Estado", "Origen", "Ubicación", "Ingreso"]
        rows: list[list[str]] = []
        for lot in lots:
            origin = "Compra" if lot.source_purchase_order_id else "Manual"
            rows.append(
                [
                    lot.lot_code,
                    lot.material.name if lot.material else "—",
                    lot.status,
                    origin,
                    lot.location or "—",
                    lot.entry_date.isoformat() if lot.entry_date else "—",
                ]
            )
        summary = [SummaryItem("Lotes trazados", str(len(lots)))]
        return columns, rows, summary

    async def _regulatory(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        lots = await self._lots.list_all()
        params = await self._parameters.get()
        regulator = params.regulatory_entity if params and params.regulatory_entity else "—"
        weight_by_symbol: dict[str, Decimal] = defaultdict(lambda: ZERO)
        fine_by_symbol: dict[str, Decimal] = defaultdict(lambda: ZERO)
        name_by_symbol: dict[str, str] = {}
        for lot in lots:
            if lot.material is None:
                continue
            sym = lot.material.symbol
            name_by_symbol[sym] = lot.material.name
            weight_by_symbol[sym] += lot.available_weight_g
            fine_by_symbol[sym] += fine_weight_g(lot.available_weight_g, lot.declared_purity)
        columns = ["Material", "Símbolo", "Peso bruto", "Peso fino"]
        rows = [
            [name_by_symbol[sym], sym, _grams(weight_by_symbol[sym]), _grams(fine_by_symbol[sym])]
            for sym in sorted(weight_by_symbol)
        ]
        summary = [
            SummaryItem("Ente regulador", regulator),
            SummaryItem("Materiales reportados", str(len(rows))),
        ]
        return columns, rows, summary

    async def _operational_kpis(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        lots = await self._lots.list_all()
        sales = await self._sales.list_all()
        purchases = await self._purchases.list_all()
        transformations = await self._transformations.list_all()
        samples = await self._samples.list_all()
        oc_pending = sum(1 for o in purchases if o.status == "pending_approval")
        ot_active = sum(1 for o in transformations if o.status == "in_progress")
        samples_pending = sum(1 for s in samples if s.result == "pending")
        columns = ["Indicador", "Valor"]
        rows = [
            ["Lotes en inventario", str(len(lots))],
            ["Órdenes de compra", str(len(purchases))],
            ["OC pendientes de aprobación", str(oc_pending)],
            ["Órdenes de venta", str(len(sales))],
            ["OT de transformación en curso", str(ot_active)],
            ["Muestras de lab pendientes", str(samples_pending)],
        ]
        summary = [SummaryItem("Indicadores", str(len(rows)))]
        return columns, rows, summary

    async def _price_analysis(self) -> tuple[list[str], list[list[str]], list[SummaryItem]]:
        lots = await self._lots.list_all()
        spot = {p.symbol: p.price_usd_per_oz for p in get_spot_prices()}
        sum_price: dict[str, Decimal] = defaultdict(lambda: ZERO)
        count: dict[str, int] = defaultdict(int)
        sym_name: dict[str, str] = {}
        for lot in lots:
            if lot.material is None:
                continue
            sym = lot.material.symbol
            sym_name[sym] = lot.material.name
            sum_price[sym] += lot.price_per_oz
            count[sym] += 1
        columns = ["Material", "Símbolo", "Precio prom. lotes", "Spot ref.", "Δ%"]
        rows: list[list[str]] = []
        for sym in sorted(sum_price):
            avg = (sum_price[sym] / count[sym]) if count[sym] else ZERO
            ref = spot.get(sym, ZERO)
            delta = ((avg - ref) / ref * 100) if ref > 0 else ZERO
            rows.append([sym_name[sym], sym, _money(avg), _money(ref), _pct(delta)])
        summary = [SummaryItem("Materiales analizados", str(len(rows)))]
        return columns, rows, summary
