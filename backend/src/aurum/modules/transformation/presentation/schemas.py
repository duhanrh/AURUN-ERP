"""Esquemas Pydantic de la API de Transformación (sección 7.4)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.inventory.domain.valuation import LotForm
from aurum.modules.transformation.application.dto import (
    NewTransformationOrder,
    TransformationKpis,
    TransformationOrderPatch,
    TransformationOrderView,
)
from aurum.modules.transformation.domain.pipeline import Process


class TransformationOrderResponse(BaseModel):
    id: uuid.UUID
    order_code: str
    input_lot_id: uuid.UUID
    input_lot_code: str
    input_material_name: str
    process: str
    input_quantity_g: Decimal
    yield_fraction: Decimal
    output_material_id: uuid.UUID
    output_material_name: str
    output_form: str
    output_purity: Decimal
    expected_output_g: Decimal
    stage: str
    status: str
    blocked: bool
    responsible: str | None
    started_at: date | None
    expected_end: date | None
    output_lot_id: uuid.UUID | None
    created_at: datetime | None
    is_deleted: bool = False

    @classmethod
    def from_view(cls, v: TransformationOrderView) -> TransformationOrderResponse:
        return cls(
            id=v.id,
            order_code=v.order_code,
            input_lot_id=v.input_lot_id,
            input_lot_code=v.input_lot_code,
            input_material_name=v.input_material_name,
            process=v.process,
            input_quantity_g=v.input_quantity_g,
            yield_fraction=v.yield_fraction,
            output_material_id=v.output_material_id,
            output_material_name=v.output_material_name,
            output_form=v.output_form,
            output_purity=v.output_purity,
            expected_output_g=v.expected_output_g,
            stage=v.stage,
            status=v.status,
            blocked=v.blocked,
            responsible=v.responsible,
            started_at=v.started_at,
            expected_end=v.expected_end,
            output_lot_id=v.output_lot_id,
            created_at=v.created_at,
            is_deleted=v.is_deleted,
        )


class TransformationKpisResponse(BaseModel):
    total_orders: int
    in_progress: int
    completed: int
    blocked: int

    @classmethod
    def from_view(cls, v: TransformationKpis) -> TransformationKpisResponse:
        return cls(
            total_orders=v.total_orders,
            in_progress=v.in_progress,
            completed=v.completed,
            blocked=v.blocked,
        )


class CreateTransformationOrderRequest(BaseModel):
    input_lot_id: uuid.UUID
    process: Process
    input_quantity_g: Decimal = Field(gt=0)
    yield_fraction: Decimal = Field(gt=0, le=1)
    output_material_id: uuid.UUID
    output_purity: Decimal = Field(gt=0, le=1)
    output_form: LotForm = "refined"
    responsible: str | None = Field(default=None, max_length=160)
    started_at: date | None = None
    expected_end: date | None = None

    def to_new_order(self) -> NewTransformationOrder:
        return NewTransformationOrder(
            input_lot_id=self.input_lot_id,
            process=self.process,
            input_quantity_g=self.input_quantity_g,
            yield_fraction=self.yield_fraction,
            output_material_id=self.output_material_id,
            output_purity=self.output_purity,
            output_form=self.output_form,
            responsible=self.responsible,
            started_at=self.started_at,
            expected_end=self.expected_end,
        )


class UpdateTransformationOrderRequest(BaseModel):
    responsible: str | None = Field(default=None, max_length=160)
    started_at: date | None = None
    expected_end: date | None = None

    def to_patch(self) -> TransformationOrderPatch:
        return TransformationOrderPatch(
            responsible=self.responsible,
            started_at=self.started_at,
            expected_end=self.expected_end,
            fields_set=frozenset(self.model_fields_set),
        )
