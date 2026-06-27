"""DTOs del módulo de Transformación."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from aurum.modules.inventory.domain.valuation import LotForm
from aurum.modules.transformation.domain.pipeline import Process, Stage, TransformationStatus


@dataclass(frozen=True, slots=True)
class TransformationOrderView:
    id: uuid.UUID
    order_code: str
    input_lot_id: uuid.UUID
    input_lot_code: str
    input_material_name: str
    process: Process
    input_quantity_g: Decimal
    yield_fraction: Decimal
    output_material_id: uuid.UUID
    output_material_name: str
    output_form: LotForm
    output_purity: Decimal
    expected_output_g: Decimal
    stage: Stage
    status: TransformationStatus
    blocked: bool
    responsible: str | None
    started_at: date | None
    expected_end: date | None
    output_lot_id: uuid.UUID | None
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class TransformationKpis:
    total_orders: int
    in_progress: int
    completed: int
    blocked: int


@dataclass(frozen=True, slots=True)
class NewTransformationOrder:
    input_lot_id: uuid.UUID
    process: Process
    input_quantity_g: Decimal
    yield_fraction: Decimal
    output_material_id: uuid.UUID
    output_purity: Decimal
    output_form: LotForm = "refined"
    responsible: str | None = None
    started_at: date | None = None
    expected_end: date | None = None
