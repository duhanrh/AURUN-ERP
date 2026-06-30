"""transformación y calidad: órdenes de proceso y muestras de lab (RLS)

Revision ID: 20260626_0005
Revises: 20260626_0004
Create Date: 2026-06-26

Fase 5. Crea las tablas por tenant ``transformation_orders`` y ``quality_samples``,
cada una con su política RLS (regla 5.5). FKs a ``inventory_lots`` y ``materials``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0005"
down_revision: str | None = "20260626_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS_TABLES = ("transformation_orders", "quality_samples")


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
    # ── transformation_orders ──
    op.create_table(
        "transformation_orders",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("order_code", sa.String(length=32), nullable=False),
        sa.Column("input_lot_id", _uuid(), nullable=False),
        sa.Column("process", sa.String(length=32), nullable=False),
        sa.Column("input_quantity_g", sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column("yield_fraction", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("output_material_id", _uuid(), nullable=False),
        sa.Column("output_form", sa.String(length=16), server_default="refined", nullable=False),
        sa.Column("output_purity", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("stage", sa.String(length=16), server_default="reception", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="in_progress", nullable=False),
        sa.Column("responsible", sa.String(length=160), nullable=True),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("expected_end", sa.Date(), nullable=True),
        sa.Column("output_lot_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_transformation_orders"),
        sa.UniqueConstraint(
            "tenant_id", "order_code", name="uq_transformation_orders_tenant_id_order_code"
        ),
        sa.ForeignKeyConstraint(
            ["input_lot_id"],
            ["inventory_lots.id"],
            name="fk_transformation_orders_inventory_lots",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["output_material_id"],
            ["materials.id"],
            name="fk_transformation_orders_materials",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["output_lot_id"],
            ["inventory_lots.id"],
            name="fk_transformation_orders_inventory_lots_output",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "stage IN ('reception', 'analysis', 'melting', 'refining', 'certified')",
            name="chk_transformation_orders_stage_valid",
        ),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed', 'cancelled')",
            name="chk_transformation_orders_status_valid",
        ),
        sa.CheckConstraint(
            "process IN ('acid_refining', 'melting_alloy', 'rolling', "
            "'granulation', 'purification')",
            name="chk_transformation_orders_process_valid",
        ),
        sa.CheckConstraint(
            "output_form IN ('raw', 'refined')", name="chk_transformation_orders_output_form_valid"
        ),
        sa.CheckConstraint(
            "input_quantity_g > 0", name="chk_transformation_orders_input_quantity_positive"
        ),
        sa.CheckConstraint(
            "yield_fraction > 0 AND yield_fraction <= 1",
            name="chk_transformation_orders_yield_fraction_valid",
        ),
    )

    # ── quality_samples ──
    op.create_table(
        "quality_samples",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("sample_code", sa.String(length=32), nullable=False),
        sa.Column("lot_id", _uuid(), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("declared_purity", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("measured_purity", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("analyst", sa.String(length=160), nullable=True),
        sa.Column("result", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("sampled_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_quality_samples"),
        sa.UniqueConstraint(
            "tenant_id", "sample_code", name="uq_quality_samples_tenant_id_sample_code"
        ),
        sa.ForeignKeyConstraint(
            ["lot_id"],
            ["inventory_lots.id"],
            name="fk_quality_samples_inventory_lots",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "method IN ('cupellation', 'xrf', 'fire_assay', 'gravimetry')",
            name="chk_quality_samples_method_valid",
        ),
        sa.CheckConstraint(
            "result IN ('pending', 'approved', 'rejected')",
            name="chk_quality_samples_result_valid",
        ),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("quality_samples")
    op.drop_table("transformation_orders")
