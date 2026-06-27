"""auditoría: registro inmutable append-only (RLS solo SELECT/INSERT)

Revision ID: 20260627_0008
Revises: 20260627_0007
Create Date: 2026-06-27

Fase 8. Crea ``audit_logs`` por tenant. La inmutabilidad (sección 4.7/7.18) se
garantiza a nivel de BD: bajo ``FORCE ROW LEVEL SECURITY`` se crean políticas
**solo** para ``SELECT`` e ``INSERT``; al no existir política para UPDATE/DELETE,
esas operaciones quedan denegadas incluso para el rol de aplicación.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260627_0008"
down_revision: str | None = "20260627_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", _uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", _uuid(), nullable=True),
        sa.Column("changes", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "idx_audit_logs_tenant_created", "audit_logs", ["tenant_id", "created_at"]
    )

    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY")
    # Append-only: solo lectura e inserción del propio tenant; sin política para
    # UPDATE/DELETE → denegadas por defecto bajo FORCE RLS.
    op.execute(
        """
        CREATE POLICY tenant_select_audit_logs
          ON audit_logs FOR SELECT
          USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY tenant_insert_audit_logs
          ON audit_logs FOR INSERT
          WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_insert_audit_logs ON audit_logs")
    op.execute("DROP POLICY IF EXISTS tenant_select_audit_logs ON audit_logs")
    op.drop_index("idx_audit_logs_tenant_created", table_name="audit_logs")
    op.drop_table("audit_logs")
