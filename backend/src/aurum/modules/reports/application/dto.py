"""DTOs del módulo de Reportes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReportTypeView:
    key: str
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class SummaryItem:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ReportTable:
    """Resultado de un reporte: cabecera con marca + tabla de datos reales."""

    key: str
    title: str
    brand_name: str
    document_number: str
    generated_at: datetime
    columns: list[str]
    rows: list[list[str]]
    summary: list[SummaryItem]
