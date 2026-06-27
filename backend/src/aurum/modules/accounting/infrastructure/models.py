"""Modelos ORM de Contabilidad: plan de cuentas, asientos y líneas (+ RLS).

- ``chart_of_accounts``: plan de cuentas por tenant.
- ``journal_entries``: cabecera de asiento (fecha, glosa, origen).
- ``ledger_entries``: líneas de débito/crédito por cuenta; la invariante de partida
  doble (Σdébitos = Σcréditos) se garantiza en la capa de aplicación/dominio.

El ``party_id``/``party_name`` (denormalizado) en la línea alimenta el submayor de
CxC/CxP por tercero sin acoplar Contabilidad al módulo de Terceros.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.modules.accounting.domain.chart import ACCOUNT_TYPES, NORMAL_BALANCES
from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

_TYPES_SQL = ", ".join(f"'{t}'" for t in ACCOUNT_TYPES)
_NORMAL_SQL = ", ".join(f"'{n}'" for n in NORMAL_BALANCES)

# Orígenes de un asiento (automático desde operación o manual).
SOURCE_TYPES = ("purchase", "sale", "sale_reversal", "payment", "manual")
_SOURCES_SQL = ", ".join(f"'{s}'" for s in SOURCE_TYPES)


class ChartAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chart_of_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_chart_of_accounts_tenant_id_code"),
        CheckConstraint(f"type IN ({_TYPES_SQL})", name="type_valid"),
        CheckConstraint(f"normal_balance IN ({_NORMAL_SQL})", name="normal_balance_valid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    normal_balance: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")


class JournalEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "entry_code", name="uq_journal_entries_tenant_id_entry_code"
        ),
        CheckConstraint(f"source_type IN ({_SOURCES_SQL})", name="source_type_valid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entry_code: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    memo: Mapped[str] = mapped_column(String(240), nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    lines: Mapped[list[LedgerEntry]] = relationship(
        back_populates="journal_entry",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="LedgerEntry.created_at",
    )


class LedgerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("debit >= 0 AND credit >= 0", name="amounts_non_negative"),
        CheckConstraint(
            "NOT (debit > 0 AND credit > 0)", name="not_both_debit_and_credit"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default="0")
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default="0")
    party_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    party_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    journal_entry: Mapped[JournalEntry] = relationship(back_populates="lines")
    account: Mapped[ChartAccount] = relationship(lazy="selectin")
