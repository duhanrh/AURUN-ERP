"""DTOs de salida del módulo de Usuarios (independientes del ORM y de la API)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RoleView:
    id: uuid.UUID
    slug: str
    name: str
    description: str
    is_system: bool
    permission_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UserView:
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    role: RoleView | None
    effective_permissions: frozenset[str]
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    is_deleted: bool = False


@dataclass(frozen=True, slots=True)
class NewUser:
    """Datos de entrada para crear un usuario (sección 7.2, ``modal-usuario``)."""

    email: str
    full_name: str
    password: str
    role_slug: str
    granted_permissions: tuple[str, ...] = field(default_factory=tuple)
    revoked_permissions: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class UserPatch:
    """Cambios parciales de un usuario; sólo se aplican los campos en ``fields_set``."""

    full_name: str | None = None
    role_slug: str | None = None
    is_active: bool | None = None
    password: str | None = None
    granted_permissions: tuple[str, ...] | None = None
    revoked_permissions: tuple[str, ...] | None = None
    fields_set: frozenset[str] = frozenset()
