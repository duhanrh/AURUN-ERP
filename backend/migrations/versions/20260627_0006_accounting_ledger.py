"""contabilidad: plan de cuentas, asientos y libro mayor (RLS)

Revision ID: 20260627_0006
Revises: 20260626_0005
Create Date: 2026-06-27

Fase 6. Crea las tablas por tenant ``chart_of_accounts``, ``journal_entries`` y
``ledger_entries``, cada una con su política RLS (regla 5.5). La invariante de
partida doble (Σdébitos = Σcréditos) se valida en la capa de aplicación.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260627_0006"
down_revision: str | None = "20260626_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS_TABLES = ("chart_of_accounts", "journal_entries", "ledger_entries")


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_{table}
          ON {table}
          USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
          WITH CHECK (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
        """
    )


def upgrade() -> None:
    # ── chart_of_accounts ──
    op.create_table(
        "chart_of_accounts",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("normal_balance", sa.String(length=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chart_of_accounts"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_chart_of_accounts_tenant_id_code"),
        sa.CheckConstraint(
            "type IN ('asset', 'liability', 'equity', 'income', 'expense')",
            name="chk_chart_of_accounts_type_valid",
        ),
        sa.CheckConstraint(
            "normal_balance IN ('debit', 'credit')",
            name="chk_chart_of_accounts_normal_balance_valid",
        ),
    )

    # ── journal_entries ──
    op.create_table(
        "journal_entries",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("entry_code", sa.String(length=32), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("memo", sa.String(length=240), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_journal_entries"),
        sa.UniqueConstraint(
            "tenant_id", "entry_code", name="uq_journal_entries_tenant_id_entry_code"
        ),
        sa.CheckConstraint(
            "source_type IN ('purchase', 'sale', 'sale_reversal', 'payment', 'manual')",
            name="chk_journal_entries_source_type_valid",
        ),
    )

    # ── ledger_entries ──
    op.create_table(
        "ledger_entries",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("journal_entry_id", _uuid(), nullable=False),
        sa.Column("account_id", _uuid(), nullable=False),
        sa.Column("debit", sa.Numeric(precision=18, scale=2), server_default="0", nullable=False),
        sa.Column("credit", sa.Numeric(precision=18, scale=2), server_default="0", nullable=False),
        sa.Column("party_id", _uuid(), nullable=True),
        sa.Column("party_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_entries"),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"], ["journal_entries.id"],
            name="fk_ledger_entries_journal_entries", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["chart_of_accounts.id"],
            name="fk_ledger_entries_chart_of_accounts", ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "debit >= 0 AND credit >= 0", name="chk_ledger_entries_amounts_non_negative"
        ),
        sa.CheckConstraint(
            "NOT (debit > 0 AND credit > 0)", name="chk_ledger_entries_not_both_debit_and_credit"
        ),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("ledger_entries")
    op.drop_table("journal_entries")
    op.drop_table("chart_of_accounts")
