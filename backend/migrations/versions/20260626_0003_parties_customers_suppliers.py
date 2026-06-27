"""terceros: maestro de clientes y proveedores (parties) con RLS

Revision ID: 20260626_0003
Revises: 20260626_0002
Create Date: 2026-06-26

Fase 3 (Terceros: Clientes y Proveedores). Crea la tabla por tenant ``parties``
(discriminada por ``kind``) con su política RLS en la misma migración que la tabla
(regla de gobierno 5.5). Sin borrado físico: la baja es ``status='inactive'``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0003"
down_revision: str | None = "20260626_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "parties",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("legal_name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=40), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("contact_name", sa.String(length=160), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("main_material", sa.String(length=80), nullable=True),
        sa.Column("certifications", sa.String(length=200), nullable=True),
        sa.Column("rating", sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column("segment", sa.String(length=60), nullable=True),
        sa.Column("preferred_material", sa.String(length=80), nullable=True),
        sa.Column("credit_limit", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_parties"),
        sa.UniqueConstraint(
            "tenant_id", "kind", "tax_id", name="uq_parties_tenant_id_kind_tax_id"
        ),
        sa.CheckConstraint("kind IN ('customer', 'supplier')", name="chk_parties_kind_valid"),
        sa.CheckConstraint(
            "status IN ('active', 'evaluation', 'inactive')", name="chk_parties_status_valid"
        ),
    )
    op.create_index("idx_parties_tenant_id_kind", "parties", ["tenant_id", "kind"])

    op.execute("ALTER TABLE parties ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE parties FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_parties
          ON parties
          USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
          WITH CHECK (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_parties ON parties")
    op.drop_index("idx_parties_tenant_id_kind", table_name="parties")
    op.drop_table("parties")
