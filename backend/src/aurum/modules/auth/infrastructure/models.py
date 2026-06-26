"""Modelo ORM de refresh tokens (sección 10.1: rotación obligatoria).

Almacena solo el **hash** del token (nunca el valor en claro). Cada uso de un
refresh token lo invalida (``revoked_at``) y registra el ``replaced_by_id`` del
token sucesor; detectar el uso de un token ya rotado es señal de robo. Tabla
por tenant (CON ``tenant_id`` + RLS).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Refresh token emitido a un usuario (rotación con detección de reutilización)."""

    __tablename__ = "refresh_tokens"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )

    @property
    def is_active(self) -> bool:
        """Activo = no revocado y no expirado (comparación en UTC naïve)."""
        from datetime import datetime as _dt

        return self.revoked_at is None and self.expires_at > _dt.utcnow()
