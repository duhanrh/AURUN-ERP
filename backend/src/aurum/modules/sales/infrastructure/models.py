"""Modelo ORM de la Orden de Venta (``sales_orders``) por tenant + RLS.

Referencia el cliente (``parties`` kind=customer) y el lote consumido. El material
y la pureza se derivan del lote; aquí sólo se guarda lo pactado en la venta.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.inventory.infrastructure.models import InventoryLot
from aurum.modules.sales.domain.order import SALES_ORDER_STATUSES
from aurum.modules.terceros.infrastructure.models import Party
from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_STATUSES_SQL = ", ".join(f"'{s}'" for s in SALES_ORDER_STATUSES)


class SalesOrder(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "sales_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_code", name="uq_sales_orders_tenant_id_order_code"),
        CheckConstraint(f"status IN ({_STATUSES_SQL})", name="status_valid"),
        CheckConstraint("quantity_g > 0", name="quantity_positive"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_code: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False
    )
    lot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_lots.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_g: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    price_per_oz: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending_payment"
    )
    invoice_number: Mapped[str | None] = mapped_column(String(40), nullable=True)

    customer: Mapped[Party] = relationship(lazy="selectin")
    lot: Mapped[InventoryLot] = relationship(lazy="selectin")
