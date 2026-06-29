"""Casos de uso del módulo de Usuarios y Roles.

Orquesta repositorios (puertos) y la lógica de dominio (permisos efectivos).
La verificación de permisos vive aquí/en presentación, nunca solo en la UI
(sección 10.2). El hashing de contraseñas se inyecta como dependencia para no
acoplar la aplicación a una librería concreta.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from aurum.modules.users.application.dto import NewUser, RoleView, UserPatch, UserView
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
from aurum.shared.errors import ConflictError, DomainError, NotFoundError

_SUPERUSER_SLUG = "superusuario"


class LastSuperuserError(DomainError):
    status_code = 409
    error_code = "last_superuser"


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
        is_deleted=user.deleted_at is not None,
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

    async def list_users(self, *, include_deleted: bool = False) -> list[UserView]:
        users = await self._users.list_all(include_deleted=include_deleted)
        return [_user_to_view(u) for u in users]

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

    async def update_user(self, user_id: uuid.UUID, patch: UserPatch) -> UserView:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        fields = patch.fields_set
        was_superuser = user.role is not None and user.role.slug == _SUPERUSER_SLUG

        if "full_name" in fields and patch.full_name is not None:
            user.full_name = patch.full_name.strip()
        if "password" in fields and patch.password:
            user.hashed_password = self._hash(patch.password)
        if "is_active" in fields and patch.is_active is not None:
            if not patch.is_active and was_superuser:
                await self._guard_last_superuser(exclude_id=user.id)
            user.is_active = patch.is_active
        if "role_slug" in fields and patch.role_slug is not None:
            role = await self._roles.get_by_slug(patch.role_slug)
            if role is None:
                raise NotFoundError(f"Rol '{patch.role_slug}' no existe en este tenant.")
            if was_superuser and role.slug != _SUPERUSER_SLUG:
                await self._guard_last_superuser(exclude_id=user.id)
            user.role_id = role.id

        if "granted_permissions" in fields or "revoked_permissions" in fields:
            user.exceptions.clear()
            await self._add_exceptions(user, patch.granted_permissions or (), granted=True)
            await self._add_exceptions(user, patch.revoked_permissions or (), granted=False)

        refreshed = await self._users.get_by_id(user.id)
        assert refreshed is not None
        return _user_to_view(refreshed)

    async def delete_user(self, user_id: uuid.UUID, *, current_user_id: uuid.UUID) -> UserView:
        if user_id == current_user_id:
            raise ConflictError("No puedes eliminar tu propio usuario.")
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        if user.role is not None and user.role.slug == _SUPERUSER_SLUG:
            await self._guard_last_superuser(exclude_id=user.id)
        user.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return _user_to_view(user)

    async def restore_user(self, user_id: uuid.UUID) -> UserView:
        user = await self._users.get_by_id(user_id, include_deleted=True)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        if user.deleted_at is None:
            raise ConflictError("El usuario no está eliminado.")
        if await self._users.exists_email(user.email, exclude_id=user.id):
            raise ConflictError(
                "No se puede restaurar: ya existe un usuario vigente con ese email."
            )
        user.deleted_at = None
        return _user_to_view(user)

    async def _guard_last_superuser(self, *, exclude_id: uuid.UUID) -> None:
        if await self._users.count_active_superusers(exclude_id=exclude_id) == 0:
            raise LastSuperuserError(
                "No se puede dejar el tenant sin un superusuario activo."
            )

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
