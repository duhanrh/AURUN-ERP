"""unidades de medida configurables por tenant (RLS + soft-delete)

Revision ID: 20260630_0012
Revises: 20260629_0011
Create Date: 2026-06-30

Sistema de plantillas de impresión (Fase 9). Crea ``units_of_measure`` por tenant
con RLS (regla 5.5) y borrado lógico (``deleted_at``). El ``code`` es único por
tenant entre las unidades vigentes (índice parcial ``WHERE deleted_at IS NULL``).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0012"
down_revision: str | None = "20260629_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
        "units_of_measure",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=False),
        sa.Column("grams_factor", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("is_base", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_units_of_measure"),
        sa.CheckConstraint("grams_factor > 0", name="chk_units_of_measure_grams_factor_positive"),
    )
    op.create_index(
        "uq_units_of_measure_tenant_id_code",
        "units_of_measure",
        ["tenant_id", "code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    _enable_rls("units_of_measure")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_units_of_measure ON units_of_measure")
    op.drop_index("uq_units_of_measure_tenant_id_code", table_name="units_of_measure")
    op.drop_table("units_of_measure")
