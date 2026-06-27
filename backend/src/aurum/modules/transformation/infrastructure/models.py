"""Modelo ORM de la Orden de Transformación (``transformation_orders``) + RLS.

Consume un lote de entrada y produce uno de salida al completarse. Guarda el proceso,
el material/pureza de salida, el rendimiento estimado y la etapa actual del pipeline.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.inventory.domain.valuation import LOT_FORMS
from aurum.modules.inventory.infrastructure.models import InventoryLot, Material
from aurum.modules.transformation.domain.pipeline import (
    PROCESSES,
    STAGE_ORDER,
    TRANSFORMATION_STATUSES,
)
from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

_STAGES_SQL = ", ".join(f"'{s}'" for s in STAGE_ORDER)
_STATUSES_SQL = ", ".join(f"'{s}'" for s in TRANSFORMATION_STATUSES)
_PROCESSES_SQL = ", ".join(f"'{p}'" for p in PROCESSES)
_FORMS_SQL = ", ".join(f"'{f}'" for f in LOT_FORMS)


class TransformationOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transformation_orders"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "order_code", name="uq_transformation_orders_tenant_id_order_code"
        ),
        CheckConstraint(f"stage IN ({_STAGES_SQL})", name="stage_valid"),
        CheckConstraint(f"status IN ({_STATUSES_SQL})", name="status_valid"),
        CheckConstraint(f"process IN ({_PROCESSES_SQL})", name="process_valid"),
        CheckConstraint(f"output_form IN ({_FORMS_SQL})", name="output_form_valid"),
        CheckConstraint("input_quantity_g > 0", name="input_quantity_positive"),
        CheckConstraint("yield_fraction > 0 AND yield_fraction <= 1", name="yield_fraction_valid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_code: Mapped[str] = mapped_column(String(32), nullable=False)
    input_lot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_lots.id", ondelete="RESTRICT"), nullable=False
    )
    process: Mapped[str] = mapped_column(String(32), nullable=False)
    input_quantity_g: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    yield_fraction: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    output_material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    output_form: Mapped[str] = mapped_column(String(16), nullable=False, server_default="refined")
    output_purity: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    stage: Mapped[str] = mapped_column(String(16), nullable=False, server_default="reception")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="in_progress")
    responsible: Mapped[str | None] = mapped_column(String(160), nullable=True)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    output_lot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_lots.id", ondelete="SET NULL"), nullable=True
    )

    input_lot: Mapped[InventoryLot] = relationship(lazy="selectin", foreign_keys=[input_lot_id])
    output_material: Mapped[Material] = relationship(lazy="selectin")
