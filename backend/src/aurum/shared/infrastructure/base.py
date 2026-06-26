"""Base declarativa de SQLAlchemy y mixins comunes.

Convenciones de la sección 4.1/4.2 del documento maestro: PK ``uuid`` generada con
``gen_random_uuid()`` (nativo en PostgreSQL 13+), timestamps de auditoría y
``naming_convention`` explícita para constraints (clave para migraciones Alembic
deterministas).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nomenclatura estable de índices/constraints (sección 4.2) para que Alembic
# genere nombres reproducibles en autogenerate.
NAMING_CONVENTION = {
    "ix": "idx_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "chk_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos ORM."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """Clave primaria ``uuid`` generada en la base de datos."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Timestamps de auditoría base (``created_at`` / ``updated_at``)."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
