"""Esquemas Pydantic de la API de Ventas (sección 7.3)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.sales.application.dto import NewSalesOrder, SalesKpis, SalesOrderView
from aurum.modules.sales.domain.order import SalesOrderStatus


class SalesOrderResponse(BaseModel):
    id: uuid.UUID
    order_code: str
    customer_id: uuid.UUID
    customer_name: str
    lot_id: uuid.UUID
    lot_code: str
    material_name: str
    declared_purity: Decimal
    quantity_g: Decimal
    price_per_oz: Decimal
    total_usd: Decimal
    status: str
    invoice_number: str | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, v: SalesOrderView) -> SalesOrderResponse:
        return cls(
            id=v.id,
            order_code=v.order_code,
            customer_id=v.customer_id,
            customer_name=v.customer_name,
            lot_id=v.lot_id,
            lot_code=v.lot_code,
            material_name=v.material_name,
            declared_purity=v.declared_purity,
            quantity_g=v.quantity_g,
            price_per_oz=v.price_per_oz,
            total_usd=v.total_usd,
            status=v.status,
            invoice_number=v.invoice_number,
            created_at=v.created_at,
        )


class SalesKpisResponse(BaseModel):
    total_orders: int
    pending_payment: int
    completed: int
    total_amount_usd: Decimal

    @classmethod
    def from_view(cls, v: SalesKpis) -> SalesKpisResponse:
        return cls(
            total_orders=v.total_orders,
            pending_payment=v.pending_payment,
            completed=v.completed,
            total_amount_usd=v.total_amount_usd,
        )


class CreateSalesOrderRequest(BaseModel):
    customer_id: uuid.UUID
    lot_id: uuid.UUID
    quantity_g: Decimal = Field(gt=0)
    price_per_oz: Decimal = Field(gt=0)
    invoice_number: str | None = Field(default=None, max_length=40)

    def to_new_order(self) -> NewSalesOrder:
        return NewSalesOrder(
            customer_id=self.customer_id,
            lot_id=self.lot_id,
            quantity_g=self.quantity_g,
            price_per_oz=self.price_per_oz,
            invoice_number=self.invoice_number,
        )


class UpdateSalesStatusRequest(BaseModel):
    status: SalesOrderStatus
