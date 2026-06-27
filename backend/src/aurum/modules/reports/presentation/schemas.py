"""Esquemas Pydantic de la API de Reportes (sección 7.15)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from aurum.modules.reports.application.dto import ReportTable, ReportTypeView


class ReportTypeResponse(BaseModel):
    key: str
    title: str
    description: str

    @classmethod
    def from_view(cls, v: ReportTypeView) -> ReportTypeResponse:
        return cls(key=v.key, title=v.title, description=v.description)


class SummaryItemResponse(BaseModel):
    label: str
    value: str


class ReportTableResponse(BaseModel):
    key: str
    title: str
    brand_name: str
    document_number: str
    generated_at: datetime
    columns: list[str]
    rows: list[list[str]]
    summary: list[SummaryItemResponse]

    @classmethod
    def from_view(cls, v: ReportTable) -> ReportTableResponse:
        return cls(
            key=v.key,
            title=v.title,
            brand_name=v.brand_name,
            document_number=v.document_number,
            generated_at=v.generated_at,
            columns=v.columns,
            rows=v.rows,
            summary=[SummaryItemResponse(label=s.label, value=s.value) for s in v.summary],
        )
