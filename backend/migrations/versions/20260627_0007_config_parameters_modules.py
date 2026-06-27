"""configuración: parámetros de negocio y módulos por tenant (RLS)

Revision ID: 20260627_0007
Revises: 20260627_0006
Create Date: 2026-06-27

Fase 7. Crea ``tenant_business_parameters`` (1:1 por tenant) y ``tenant_module_config``
(una fila por módulo activable), ambas con RLS (regla 5.5). La marca personalizada
ya vive en ``tenant_branding`` (Fase 1).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260627_0007"
down_revision: str | None = "20260627_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS_TABLES = ("tenant_business_parameters", "tenant_module_config")


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
        "tenant_business_parameters",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("base_currency", sa.String(length=8), server_default="USD", nullable=False),
        sa.Column("weight_unit", sa.String(length=4), server_default="g", nullable=False),
        sa.Column("min_stock_g", sa.Numeric(precision=16, scale=4), server_default="1000", nullable=False),
        sa.Column("min_margin_pct", sa.Numeric(precision=6, scale=2), server_default="5", nullable=False),
        sa.Column("language", sa.String(length=8), server_default="es", nullable=False),
        sa.Column("timezone", sa.String(length=48), server_default="America/Bogota", nullable=False),
        sa.Column("date_format", sa.String(length=16), server_default="YYYY-MM-DD", nullable=False),
        sa.Column("regulatory_entity", sa.String(length=120), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_business_parameters"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_business_parameters_tenant_id"),
    )

    op.create_table(
        "tenant_module_config",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("module_key", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_module_config"),
        sa.UniqueConstraint(
            "tenant_id", "module_key", name="uq_tenant_module_config_tenant_id_module_key"
        ),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("tenant_module_config")
    op.drop_table("tenant_business_parameters")
