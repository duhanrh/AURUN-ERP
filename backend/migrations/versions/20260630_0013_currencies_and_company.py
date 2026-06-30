"""monedas configurables y datos del comercio/empresa por tenant (RLS)

Revision ID: 20260630_0013
Revises: 20260630_0012
Create Date: 2026-06-30

Sistema de plantillas de impresión (Fase 9). Crea ``currencies`` (CRUD con baja
lógica, una base por tenant) y ``tenant_company`` (1:1, datos legales/fiscales para
las cabeceras de documentos), ambas con RLS (regla 5.5).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0013"
down_revision: str | None = "20260630_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS_TABLES = ("currencies", "tenant_company")


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
    op.create_table(
        "currencies",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=False),
        sa.Column("decimals", sa.Integer(), server_default="2", nullable=False),
        sa.Column("is_base", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_currencies"),
        sa.CheckConstraint("decimals >= 0 AND decimals <= 6", name="chk_currencies_decimals_range"),
    )
    op.create_index(
        "uq_currencies_tenant_id_code",
        "currencies",
        ["tenant_id", "code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "tenant_company",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("legal_name", sa.String(length=160), server_default="", nullable=False),
        sa.Column("trade_name", sa.String(length=160), server_default="", nullable=False),
        sa.Column("tax_id", sa.String(length=40), server_default="", nullable=False),
        sa.Column("tax_regime", sa.String(length=80), server_default="", nullable=False),
        sa.Column("address", sa.String(length=200), server_default="", nullable=False),
        sa.Column("city", sa.String(length=80), server_default="", nullable=False),
        sa.Column("phone", sa.String(length=40), server_default="", nullable=False),
        sa.Column("email", sa.String(length=160), server_default="", nullable=False),
        sa.Column("website", sa.String(length=200), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_company"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_company_tenant_id"),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("tenant_company")
    op.drop_index("uq_currencies_tenant_id_code", table_name="currencies")
    op.drop_table("currencies")
