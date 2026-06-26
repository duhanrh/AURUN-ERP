"""Puertos (Protocols) del módulo de Usuarios — contratos de persistencia.

La capa de aplicación depende de estas abstracciones, no de SQLAlchemy. La
infraestructura las implementa (``infrastructure.repositories``). Inversión de
dependencias (Clean Architecture).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from aurum.modules.users.infrastructure.models import (
    Permission,
    Role,
    User,
)


class PermissionRepository(Protocol):
    async def get_by_code(self, code: str) -> Permission | None: ...
    async def list_all(self) -> list[Permission]: ...


class RoleRepository(Protocol):
    async def get_by_slug(self, slug: str) -> Role | None: ...
    async def list_all(self) -> list[Role]: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def list_all(self) -> list[User]: ...
    async def add(self, user: User) -> User: ...
    async def exists_email(self, email: str) -> bool: ...
