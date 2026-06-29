"""Modelos ORM del Inventario (``materials``, ``inventory_lots``) por tenant + RLS.

Un lote referencia su material (catálogo del tenant) y opcionalmente su proveedor
de origen (``parties``). ``gross_weight_g`` es el peso de entrada; ``available_weight_g``
es el stock vivo que las ventas reducen (nunca por debajo de 0, sección 7.3).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.inventory.domain.valuation import LOT_FORMS, LOT_STATUSES
from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_FORMS_SQL = ", ".join(f"'{f}'" for f in LOT_FORMS)
_STATUSES_SQL = ", ".join(f"'{s}'" for s in LOT_STATUSES)


class Material(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Material del catálogo del tenant (Oro 24K, Plata .999, …)."""

    __tablename__ = "materials"
    __table_args__ = (
        Index(
            "uq_materials_tenant_id_code",
            "tenant_id",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class InventoryLot(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Lote de material en inventario, con trazabilidad de origen y stock vivo."""

    __tablename__ = "inventory_lots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "lot_code", name="uq_inventory_lots_tenant_id_lot_code"),
        CheckConstraint(f"form IN ({_FORMS_SQL})", name="form_valid"),
        CheckConstraint(f"status IN ({_STATUSES_SQL})", name="status_valid"),
        CheckConstraint("available_weight_g >= 0", name="available_non_negative"),
        CheckConstraint("declared_purity > 0 AND declared_purity <= 1", name="purity_fraction"),
        Index("idx_inventory_lots_tenant_id_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    lot_code: Mapped[str] = mapped_column(String(32), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    form: Mapped[str] = mapped_column(String(16), nullable=False, server_default="raw")
    declared_purity: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    gross_weight_g: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    available_weight_g: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    price_per_oz: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="available")
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parties.id", ondelete="SET NULL"), nullable=True
    )
    source_purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    material: Mapped[Material] = relationship(lazy="selectin")
