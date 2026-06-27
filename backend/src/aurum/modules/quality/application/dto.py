"""DTOs del módulo de Calidad."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from aurum.modules.quality.domain.sample import AnalysisMethod, SampleResult


@dataclass(frozen=True, slots=True)
class QualitySampleView:
    id: uuid.UUID
    sample_code: str
    lot_id: uuid.UUID
    lot_code: str
    material_name: str
    method: AnalysisMethod
    declared_purity: Decimal
    measured_purity: Decimal
    difference: Decimal
    analyst: str | None
    result: SampleResult
    sampled_at: date | None
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class QualityKpis:
    total_samples: int
    approved: int
    rejected: int
    pending: int


@dataclass(frozen=True, slots=True)
class NewSample:
    lot_id: uuid.UUID
    method: AnalysisMethod
    measured_purity: Decimal
    result: SampleResult = "pending"
    analyst: str | None = None
    sampled_at: date | None = None
