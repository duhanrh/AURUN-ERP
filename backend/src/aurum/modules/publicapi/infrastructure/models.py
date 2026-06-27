"""Modelo ORM de las API Keys (``api_keys``).

Tabla de **plataforma** (sin RLS, como ``tenants``/``permissions``, sección 5.4):
la autenticación de la API pública debe localizar la clave por su ``prefix`` sin un
tenant aún resuelto. La columna ``tenant_id`` asocia cada clave a un único tenant;
una vez autenticada, las respuestas pasan por el ``TenantContext`` y la RLS normal.
Solo se guarda el ``secret_hash`` (nunca el secreto en claro).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (Index("idx_api_keys_tenant_id", "tenant_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prefix: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
