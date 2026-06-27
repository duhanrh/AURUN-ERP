"""Catálogo de reportes (sección 7.15): los 6 tipos prototipados en la maqueta.

Cada reporte se genera con **datos reales del tenant autenticado** y comparte el
formato de cabecera con marca/fecha/número de documento del prototipo (`report-brand`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

ReportKey = Literal[
    "inventory_valued",
    "profit_loss",
    "lot_traceability",
    "regulatory",
    "operational_kpis",
    "price_analysis",
]

REPORT_KEYS: tuple[ReportKey, ...] = get_args(ReportKey)


@dataclass(frozen=True, slots=True)
class ReportDef:
    key: ReportKey
    title: str
    description: str


REPORT_CATALOG: tuple[ReportDef, ...] = (
    ReportDef(
        "inventory_valued",
        "Inventario Valorizado",
        "Lotes en stock con su valorización a precio pactado.",
    ),
    ReportDef(
        "profit_loss", "Pérdidas y Ganancias", "Ingresos, costos y utilidad neta del período."
    ),
    ReportDef(
        "lot_traceability", "Trazabilidad de Lotes", "Origen, estado y proveedor de cada lote."
    ),
    ReportDef(
        "regulatory", "Informe Regulatorio", "Resumen por material para el ente regulador."
    ),
    ReportDef(
        "operational_kpis", "KPIs Operativos", "Indicadores clave de operación del tenant."
    ),
    ReportDef(
        "price_analysis",
        "Análisis de Precios",
        "Precio promedio por material vs referencia spot.",
    ),
)

REPORT_BY_KEY: dict[str, ReportDef] = {r.key: r for r in REPORT_CATALOG}
