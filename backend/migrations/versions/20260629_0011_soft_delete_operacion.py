"""baja lógica: deleted_at en documentos de operación (OC, OV, OT, muestras)

Revision ID: 20260629_0011
Revises: 20260629_0010
Create Date: 2026-06-29

Ola 2 del CRUD con borrado lógico: añade ``deleted_at`` (nullable) a las tablas de
documentos de operación. ``inventory_lots`` ya lo recibió en la Ola 0010.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0011"
down_revision: str | None = "20260629_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "purchase_orders",
    "sales_orders",
    "transformation_orders",
    "quality_samples",
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_column(table, "deleted_at")
