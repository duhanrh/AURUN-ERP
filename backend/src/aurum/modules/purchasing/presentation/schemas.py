"""Esquemas Pydantic de la API de Compras (sección 7.2)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.inventory.domain.valuation import LotForm
from aurum.modules.purchasing.application.dto import (
    NewPurchaseOrder,
    PurchaseOrderPatch,
    PurchaseOrderView,
    PurchasingKpis,
)


class PurchaseOrderResponse(BaseModel):
    id: uuid.UUID
    order_code: str
    supplier_id: uuid.UUID
    supplier_name: str
    material_id: uuid.UUID
    material_name: str
    quantity_g: Decimal
    declared_purity: Decimal
    form: str
    price_per_oz: Decimal
    total_usd: Decimal
    location: str | None
    expected_delivery: date | None
    status: str
    lot_id: uuid.UUID | None
    created_at: datetime | None
    is_deleted: bool = False

    @classmethod
    def from_view(cls, v: PurchaseOrderView) -> PurchaseOrderResponse:
        return cls(
            id=v.id,
            order_code=v.order_code,
            supplier_id=v.supplier_id,
            supplier_name=v.supplier_name,
            material_id=v.material_id,
            material_name=v.material_name,
            quantity_g=v.quantity_g,
            declared_purity=v.declared_purity,
            form=v.form,
            price_per_oz=v.price_per_oz,
            total_usd=v.total_usd,
            location=v.location,
            expected_delivery=v.expected_delivery,
            status=v.status,
            lot_id=v.lot_id,
            created_at=v.created_at,
            is_deleted=v.is_deleted,
        )


class PurchasingKpisResponse(BaseModel):
    total_orders: int
    pending_approval: int
    approved: int
    total_amount_usd: Decimal

    @classmethod
    def from_view(cls, v: PurchasingKpis) -> PurchasingKpisResponse:
        return cls(
            total_orders=v.total_orders,
            pending_approval=v.pending_approval,
            approved=v.approved,
            total_amount_usd=v.total_amount_usd,
        )


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: uuid.UUID
    material_id: uuid.UUID
    quantity_g: Decimal = Field(gt=0)
    declared_purity: Decimal = Field(gt=0, le=1)
    price_per_oz: Decimal = Field(gt=0)
    form: LotForm = "raw"
    location: str | None = Field(default=None, max_length=120)
    expected_delivery: date | None = None
    notes: str | None = None

    def to_new_order(self) -> NewPurchaseOrder:
        return NewPurchaseOrder(
            supplier_id=self.supplier_id,
            material_id=self.material_id,
            quantity_g=self.quantity_g,
            declared_purity=self.declared_purity,
            price_per_oz=self.price_per_oz,
            form=self.form,
            location=self.location,
            expected_delivery=self.expected_delivery,
            notes=self.notes,
        )


class UpdatePurchaseOrderRequest(BaseModel):
    quantity_g: Decimal | None = Field(default=None, gt=0)
    declared_purity: Decimal | None = Field(default=None, gt=0, le=1)
    price_per_oz: Decimal | None = Field(default=None, gt=0)
    form: LotForm | None = None
    location: str | None = Field(default=None, max_length=120)
    expected_delivery: date | None = None
    notes: str | None = None

    def to_patch(self) -> PurchaseOrderPatch:
        return PurchaseOrderPatch(
            quantity_g=self.quantity_g,
            declared_purity=self.declared_purity,
            price_per_oz=self.price_per_oz,
            form=self.form,
            location=self.location,
            expected_delivery=self.expected_delivery,
            notes=self.notes,
            fields_set=frozenset(self.model_fields_set),
        )
