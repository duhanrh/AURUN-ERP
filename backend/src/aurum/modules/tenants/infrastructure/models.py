"""Modelos ORM del módulo de Tenants.

- ``tenants``: catálogo de plataforma (SIN ``tenant_id``, sin RLS — excepción
  explícita de la sección 5.4).
- ``tenant_branding``: personalización 1:1 por tenant (CON ``tenant_id`` + RLS,
  sección 5.6). Si ``is_customized`` es false, el frontend aplica el tema "Aurum".
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Empresa suscriptora de la plataforma."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    subscription_plan: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="free"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    branding: Mapped[TenantBranding] = relationship(
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
    )


class TenantBranding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Identidad visual personalizada de un tenant (1:1 con ``tenants``)."""

    __tablename__ = "tenant_branding"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    brand_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(160), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    color_primary: Mapped[str | None] = mapped_column(String(9), nullable=True)
    color_background: Mapped[str | None] = mapped_column(String(9), nullable=True)
    color_success: Mapped[str | None] = mapped_column(String(9), nullable=True)
    color_danger: Mapped[str | None] = mapped_column(String(9), nullable=True)

    is_customized: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    tenant: Mapped[Tenant] = relationship(back_populates="branding")
