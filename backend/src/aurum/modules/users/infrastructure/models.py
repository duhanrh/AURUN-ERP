"""Modelos ORM del módulo de Usuarios, Roles y Permisos (RBAC, sección 10.2).

Tenancy (sección 5.4):
- ``permissions``: catálogo de **plataforma** (SIN ``tenant_id``, sin RLS); se
  versiona en código (``domain.permissions``) y se siembra una sola vez.
- ``roles``, ``users``, ``role_permissions``, ``user_permission_exceptions``:
  datos **por tenant** (CON ``tenant_id`` + RLS). Los roles base se siembran en el
  provisionamiento de cada tenant (sección 5.7).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Permiso del catálogo de plataforma (``recurso:accion``)."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    resource: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Rol de un tenant que agrupa permisos (RBAC)."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_roles_tenant_id_slug"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    slug: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Objeto-asociación explícito (no ``secondary``) para poder fijar ``tenant_id``
    # en cada vínculo y que la política RLS de ``role_permissions`` lo acepte.
    permission_links: Mapped[list[RolePermission]] = relationship(
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def permissions(self) -> list[Permission]:
        return [link.permission for link in self.permission_links]


class RolePermission(Base):
    """Asociación rol↔permiso (con ``tenant_id`` para que RLS la proteja)."""

    __tablename__ = "role_permissions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[Role] = relationship(back_populates="permission_links")
    permission: Mapped[Permission] = relationship(lazy="selectin")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Usuario perteneciente a un tenant."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[Role | None] = relationship(lazy="selectin")

    exceptions: Mapped[list[UserPermissionException]] = relationship(
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class UserPermissionException(Base):
    """Excepción de permiso por usuario (otorga/revoca sin cambiar de rol, 10.3)."""

    __tablename__ = "user_permission_exceptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    user: Mapped[User] = relationship(back_populates="exceptions")
    permission: Mapped[Permission] = relationship(lazy="selectin")
