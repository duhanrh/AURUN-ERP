"""initial: tenants y tenant_branding (con RLS)

Revision ID: 20260626_0001
Revises:
Create Date: 2026-06-26

Crea el núcleo multi-tenant de la plataforma:
- ``tenants``: catálogo de plataforma (sin tenant_id / sin RLS, excepción 5.4).
- ``tenant_branding``: 1:1 por tenant, CON tenant_id + política RLS (secciones 5.4-5.6).

La política RLS se crea en esta misma migración que crea la tabla (regla de
gobierno 5.5: nunca dejar una ventana sin protección).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("subdomain", sa.String(length=63), nullable=False),
        sa.Column(
            "subscription_plan",
            sa.String(length=40),
            server_default="free",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.UniqueConstraint("subdomain", name="uq_tenants_subdomain"),
    )

    op.create_table(
        "tenant_branding",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_name", sa.String(length=160), nullable=True),
        sa.Column("tagline", sa.String(length=160), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("color_primary", sa.String(length=9), nullable=True),
        sa.Column("color_background", sa.String(length=9), nullable=True),
        sa.Column("color_success", sa.String(length=9), nullable=True),
        sa.Column("color_danger", sa.String(length=9), nullable=True),
        sa.Column("is_customized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_branding"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_tenant_branding_tenants",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_branding_tenant_id"),
    )

    # ── Row Level Security en tenant_branding (sección 5.5) ──
    # Se usa current_setting(..., true) (missing_ok) para no lanzar error cuando la
    # variable no está fijada; en ese caso la comparación es NULL → no se ven filas.
    op.execute("ALTER TABLE tenant_branding ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_branding FORCE ROW LEVEL SECURITY")
    # NULLIF(..., '') hace que tanto la variable sin fijar (NULL) como una cadena
    # vacía denieguen por defecto, evitando además el error de castear ''::uuid.
    op.execute(
        """
        CREATE POLICY tenant_isolation_tenant_branding
          ON tenant_branding
          USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
          WITH CHECK (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
          )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tenant_branding ON tenant_branding")
    op.drop_table("tenant_branding")
    op.drop_table("tenants")
