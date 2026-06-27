"""Esquemas Pydantic de la API de Calidad (sección 7.5)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.quality.application.dto import NewSample, QualityKpis, QualitySampleView
from aurum.modules.quality.domain.sample import AnalysisMethod, SampleResult


class QualitySampleResponse(BaseModel):
    id: uuid.UUID
    sample_code: str
    lot_id: uuid.UUID
    lot_code: str
    material_name: str
    method: str
    declared_purity: Decimal
    measured_purity: Decimal
    difference: Decimal
    analyst: str | None
    result: str
    sampled_at: date | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, v: QualitySampleView) -> QualitySampleResponse:
        return cls(
            id=v.id,
            sample_code=v.sample_code,
            lot_id=v.lot_id,
            lot_code=v.lot_code,
            material_name=v.material_name,
            method=v.method,
            declared_purity=v.declared_purity,
            measured_purity=v.measured_purity,
            difference=v.difference,
            analyst=v.analyst,
            result=v.result,
            sampled_at=v.sampled_at,
            created_at=v.created_at,
        )


class QualityKpisResponse(BaseModel):
    total_samples: int
    approved: int
    rejected: int
    pending: int

    @classmethod
    def from_view(cls, v: QualityKpis) -> QualityKpisResponse:
        return cls(
            total_samples=v.total_samples,
            approved=v.approved,
            rejected=v.rejected,
            pending=v.pending,
        )


class CreateSampleRequest(BaseModel):
    lot_id: uuid.UUID
    method: AnalysisMethod
    measured_purity: Decimal = Field(gt=0, le=1)
    result: SampleResult = "pending"
    analyst: str | None = Field(default=None, max_length=160)
    sampled_at: date | None = None

    def to_new_sample(self) -> NewSample:
        return NewSample(
            lot_id=self.lot_id,
            method=self.method,
            measured_purity=self.measured_purity,
            result=self.result,
            analyst=self.analyst,
            sampled_at=self.sampled_at,
        )
