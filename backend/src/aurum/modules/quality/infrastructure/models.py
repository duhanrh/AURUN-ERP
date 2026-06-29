"""Modelo ORM de la Muestra de Laboratorio (``quality_samples``) + RLS.

Compara la pureza declarada del lote con la medida. La diferencia se calcula en la
capa de aplicación. Un resultado ``rejected`` deja el lote de origen en cuarentena.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.inventory.infrastructure.models import InventoryLot
from aurum.modules.quality.domain.sample import ANALYSIS_METHODS, SAMPLE_RESULTS
from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_METHODS_SQL = ", ".join(f"'{m}'" for m in ANALYSIS_METHODS)
_RESULTS_SQL = ", ".join(f"'{r}'" for r in SAMPLE_RESULTS)


class QualitySample(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "quality_samples"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "sample_code", name="uq_quality_samples_tenant_id_sample_code"
        ),
        CheckConstraint(f"method IN ({_METHODS_SQL})", name="method_valid"),
        CheckConstraint(f"result IN ({_RESULTS_SQL})", name="result_valid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sample_code: Mapped[str] = mapped_column(String(32), nullable=False)
    lot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_lots.id", ondelete="RESTRICT"), nullable=False
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    declared_purity: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    measured_purity: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    analyst: Mapped[str | None] = mapped_column(String(160), nullable=True)
    result: Mapped[str] = mapped_column(String(16), nullable=False, server_default="pending")
    sampled_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    lot: Mapped[InventoryLot] = relationship(lazy="selectin")
