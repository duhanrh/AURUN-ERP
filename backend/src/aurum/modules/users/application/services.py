"""Casos de uso del módulo de Usuarios y Roles.

Orquesta repositorios (puertos) y la lógica de dominio (permisos efectivos).
La verificación de permisos vive aquí/en presentación, nunca solo en la UI
(sección 10.2). El hashing de contraseñas se inyecta como dependencia para no
acoplar la aplicación a una librería concreta.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from aurum.modules.users.application.dto import NewUser, RoleView, UserView
from aurum.modules.users.application.ports import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
)
from aurum.modules.users.domain.authorization import compute_effective_permissions
from aurum.modules.users.infrastructure.models import (
    Role,
    User,
    UserPermissionException,
)
from aurum.shared.errors import ConflictError, NotFoundError


def _role_to_view(role: Role) -> RoleView:
    return RoleView(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permission_codes=tuple(sorted(p.code for p in role.permissions)),
    )


def _effective_permissions(user: User) -> frozenset[str]:
    role_codes = [p.code for p in user.role.permissions] if user.role else []
    granted = [e.permission.code for e in user.exceptions if e.granted]
    revoked = [e.permission.code for e in user.exceptions if not e.granted]
    return compute_effective_permissions(role_codes, granted, revoked)


def _user_to_view(user: User) -> UserView:
    return UserView(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=_role_to_view(user.role) if user.role else None,
        effective_permissions=_effective_permissions(user),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


class UserService:
    """Gestión de usuarios y consulta de roles del tenant activo."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        users: UserRepository,
        roles: RoleRepository,
        permissions: PermissionRepository,
        password_hasher: Callable[[str], str],
    ) -> None:
        self._tenant_id = tenant_id
        self._users = users
        self._roles = roles
        self._permissions = permissions
        self._hash = password_hasher

    async def list_roles(self) -> list[RoleView]:
        return [_role_to_view(r) for r in await self._roles.list_all()]

    async def list_users(self) -> list[UserView]:
        return [_user_to_view(u) for u in await self._users.list_all()]

    async def get_user(self, user_id: uuid.UUID) -> UserView:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        return _user_to_view(user)

    async def create_user(self, data: NewUser) -> UserView:
        if await self._users.exists_email(data.email):
            raise ConflictError("Ya existe un usuario con ese email en este tenant.")

        role = await self._roles.get_by_slug(data.role_slug)
        if role is None:
            raise NotFoundError(f"Rol '{data.role_slug}' no existe en este tenant.")

        user = User(
            tenant_id=self._tenant_id,
            email=data.email,
            full_name=data.full_name,
            hashed_password=self._hash(data.password),
            role_id=role.id,
            is_active=True,
        )
        await self._add_exceptions(user, data.granted_permissions, granted=True)
        await self._add_exceptions(user, data.revoked_permissions, granted=False)

        await self._users.add(user)
        # Recargar para materializar relaciones (role/exceptions) en la vista.
        created = await self._users.get_by_id(user.id)
        assert created is not None
        return _user_to_view(created)

    async def _add_exceptions(
        self, user: User, codes: tuple[str, ...], *, granted: bool
    ) -> None:
        for code in codes:
            permission = await self._permissions.get_by_code(code)
            if permission is None:
                raise NotFoundError(f"Permiso '{code}' no existe en el catálogo.")
            user.exceptions.append(
                UserPermissionException(
                    tenant_id=self._tenant_id,
                    permission_id=permission.id,
                    granted=granted,
                )
            )
