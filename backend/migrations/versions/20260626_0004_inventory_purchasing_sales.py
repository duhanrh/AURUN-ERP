"""operación: materiales, lotes, órdenes de compra y de venta (RLS)

Revision ID: 20260626_0004
Revises: 20260626_0003
Create Date: 2026-06-26

Fase 4 (Operación). Crea las tablas por tenant ``materials``, ``inventory_lots``,
``purchase_orders`` y ``sales_orders``, cada una con su política RLS en la misma
migración (regla de gobierno 5.5). Las FK a ``parties`` provienen de la Fase 3.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0004"
down_revision: str | None = "20260626_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS_TABLES = ("materials", "inventory_lots", "purchase_orders", "sales_orders")


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
    # ── materials ──
    op.create_table(
        "materials",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_materials"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_materials_tenant_id_code"),
    )

    # ── inventory_lots ──
    op.create_table(
        "inventory_lots",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("lot_code", sa.String(length=32), nullable=False),
        sa.Column("material_id", _uuid(), nullable=False),
        sa.Column("form", sa.String(length=16), server_default="raw", nullable=False),
        sa.Column("declared_purity", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("gross_weight_g", sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column("available_weight_g", sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column("price_per_oz", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="available", nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=True),
        sa.Column("supplier_id", _uuid(), nullable=True),
        sa.Column("source_purchase_order_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_lots"),
        sa.UniqueConstraint("tenant_id", "lot_code", name="uq_inventory_lots_tenant_id_lot_code"),
        sa.ForeignKeyConstraint(
            ["material_id"], ["materials.id"], name="fk_inventory_lots_materials",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"], ["parties.id"], name="fk_inventory_lots_parties", ondelete="SET NULL"
        ),
        sa.CheckConstraint("form IN ('raw', 'refined')", name="chk_inventory_lots_form_valid"),
        sa.CheckConstraint(
            "status IN ('available', 'reserved', 'in_process', 'low_stock', 'quarantine')",
            name="chk_inventory_lots_status_valid",
        ),
        sa.CheckConstraint(
            "available_weight_g >= 0", name="chk_inventory_lots_available_non_negative"
        ),
        sa.CheckConstraint(
            "declared_purity > 0 AND declared_purity <= 1", name="chk_inventory_lots_purity_fraction"
        ),
    )
    op.create_index(
        "idx_inventory_lots_tenant_id_status", "inventory_lots", ["tenant_id", "status"]
    )

    # ── purchase_orders ──
    op.create_table(
        "purchase_orders",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("order_code", sa.String(length=32), nullable=False),
        sa.Column("supplier_id", _uuid(), nullable=False),
        sa.Column("material_id", _uuid(), nullable=False),
        sa.Column("quantity_g", sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column("declared_purity", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("form", sa.String(length=16), server_default="raw", nullable=False),
        sa.Column("price_per_oz", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("expected_delivery", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending_approval", nullable=False),
        sa.Column("lot_id", _uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_purchase_orders"),
        sa.UniqueConstraint(
            "tenant_id", "order_code", name="uq_purchase_orders_tenant_id_order_code"
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"], ["parties.id"], name="fk_purchase_orders_parties", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["material_id"], ["materials.id"], name="fk_purchase_orders_materials",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["lot_id"], ["inventory_lots.id"], name="fk_purchase_orders_inventory_lots",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "status IN ('pending_approval', 'approved', 'rejected', 'cancelled')",
            name="chk_purchase_orders_status_valid",
        ),
        sa.CheckConstraint("form IN ('raw', 'refined')", name="chk_purchase_orders_form_valid"),
        sa.CheckConstraint("quantity_g > 0", name="chk_purchase_orders_quantity_positive"),
    )

    # ── sales_orders ──
    op.create_table(
        "sales_orders",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("order_code", sa.String(length=32), nullable=False),
        sa.Column("customer_id", _uuid(), nullable=False),
        sa.Column("lot_id", _uuid(), nullable=False),
        sa.Column("quantity_g", sa.Numeric(precision=16, scale=4), nullable=False),
        sa.Column("price_per_oz", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending_payment", nullable=False),
        sa.Column("invoice_number", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_sales_orders"),
        sa.UniqueConstraint("tenant_id", "order_code", name="uq_sales_orders_tenant_id_order_code"),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["parties.id"], name="fk_sales_orders_parties", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["lot_id"], ["inventory_lots.id"], name="fk_sales_orders_inventory_lots",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('pending_payment', 'preparing', 'completed', 'cancelled')",
            name="chk_sales_orders_status_valid",
        ),
        sa.CheckConstraint("quantity_g > 0", name="chk_sales_orders_quantity_positive"),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
    op.drop_table("sales_orders")
    op.drop_table("purchase_orders")
    op.drop_index("idx_inventory_lots_tenant_id_status", table_name="inventory_lots")
    op.drop_table("inventory_lots")
    op.drop_table("materials")
