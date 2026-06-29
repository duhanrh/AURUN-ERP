"""Modelo ORM del maestro de Terceros (``parties``), por tenant + RLS (sección 5.4).

Una sola tabla discriminada por ``kind`` cubre clientes y proveedores: comparten
identidad (razón social, NIT/documento, ubicación) y contacto, y cada tipo usa el
subconjunto de columnas que le aplica (segmento/línea de crédito para clientes;
material principal/certificaciones/rating para proveedores). Las columnas del otro
tipo quedan ``NULL``. Los saldos y volúmenes operativos (CxC/CxP, compras, órdenes)
se derivarán de Operación en Fase 4; aquí solo vive el dato maestro.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aurum.modules.terceros.domain.party import PARTY_KINDS, PARTY_STATUSES
from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_KINDS_SQL = ", ".join(f"'{k}'" for k in PARTY_KINDS)
_STATUSES_SQL = ", ".join(f"'{s}'" for s in PARTY_STATUSES)


class Party(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Tercero del tenant (cliente o proveedor)."""

    __tablename__ = "parties"
    __table_args__ = (
        # Unicidad de NIT solo entre terceros vigentes (un borrado libera el NIT).
        Index(
            "uq_parties_tenant_id_kind_tax_id",
            "tenant_id",
            "kind",
            "tax_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint(f"kind IN ({_KINDS_SQL})", name="kind_valid"),
        CheckConstraint(f"status IN ({_STATUSES_SQL})", name="status_valid"),
        Index("idx_parties_tenant_id_kind", "tenant_id", "kind"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    # ── Identidad y contacto (común) ──
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(40), nullable=False)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Específico de proveedor ──
    main_material: Mapped[str | None] = mapped_column(String(80), nullable=True)
    certifications: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)

    # ── Específico de cliente ──
    segment: Mapped[str | None] = mapped_column(String(60), nullable=True)
    preferred_material: Mapped[str | None] = mapped_column(String(80), nullable=True)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
