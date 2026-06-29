"""baja lógica: deleted_at en datos maestros (parties, users, materials, lots)

Revision ID: 20260629_0010
Revises: 20260627_0009
Create Date: 2026-06-29

Ola 1 del CRUD con borrado lógico: añade ``deleted_at`` (nullable) a las tablas de
datos maestros. Nulo = vigente; con valor = eliminado. Es ortogonal al estado de
negocio (``status``/``is_active``). Se incluye ``inventory_lots`` para preparar la
Ola 2 (su endpoint de baja llega después; la columna ya filtra desde ahora).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0010"
down_revision: str | None = "20260627_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("parties", "users", "materials", "inventory_lots")

# (constraint_actual, tabla, columnas, where) → índice único parcial que respeta la
# baja lógica: la unicidad solo aplica entre filas vigentes (``deleted_at IS NULL``).
_PARTIAL_UNIQUE = (
    ("uq_parties_tenant_id_kind_tax_id", "parties", ["tenant_id", "kind", "tax_id"]),
    ("uq_users_tenant_id_email", "users", ["tenant_id", "email"]),
    ("uq_materials_tenant_id_code", "materials", ["tenant_id", "code"]),
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))
    # Reemplaza las restricciones únicas plenas por índices únicos parciales.
    for name, table, cols in _PARTIAL_UNIQUE:
        op.drop_constraint(name, table, type_="unique")
        op.create_index(
            name, table, cols, unique=True, postgresql_where=sa.text("deleted_at IS NULL")
        )


def downgrade() -> None:
    for name, table, cols in _PARTIAL_UNIQUE:
        op.drop_index(name, table_name=table)
        op.create_unique_constraint(name, table, cols)
    for table in reversed(_TABLES):
        op.drop_column(table, "deleted_at")
