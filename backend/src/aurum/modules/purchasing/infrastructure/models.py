"""Modelo ORM de la Orden de Compra (``purchase_orders``) por tenant + RLS.

Captura los términos pactados (material, peso, pureza, precio/oz, entrega). Al
aprobarse se enlaza con el lote que genera (``lot_id``). El proveedor referencia
``parties`` (kind=supplier); el material, el catálogo del tenant.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.inventory.domain.valuation import LOT_FORMS
from aurum.modules.inventory.infrastructure.models import Material
from aurum.modules.purchasing.domain.order import PURCHASE_ORDER_STATUSES
from aurum.modules.terceros.infrastructure.models import Party
from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_STATUSES_SQL = ", ".join(f"'{s}'" for s in PURCHASE_ORDER_STATUSES)
_FORMS_SQL = ", ".join(f"'{f}'" for f in LOT_FORMS)


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "order_code", name="uq_purchase_orders_tenant_id_order_code"
        ),
        CheckConstraint(f"status IN ({_STATUSES_SQL})", name="status_valid"),
        CheckConstraint(f"form IN ({_FORMS_SQL})", name="form_valid"),
        CheckConstraint("quantity_g > 0", name="quantity_positive"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_code: Mapped[str] = mapped_column(String(32), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_g: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    declared_purity: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    form: Mapped[str] = mapped_column(String(16), nullable=False, server_default="raw")
    price_per_oz: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending_approval"
    )
    lot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_lots.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    material: Mapped[Material] = relationship(lazy="selectin")
    supplier: Mapped[Party] = relationship(lazy="selectin")
