"""Implementaciones SQLAlchemy de los puertos del módulo de Usuarios.

Operan dentro de una sesión ya acotada al tenant (RLS aplicado en ``get_session``),
por lo que las consultas no necesitan filtrar ``tenant_id`` manualmente: la base de
datos lo hace por nosotros (defensa en profundidad, sección 5.5).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.users.infrastructure.models import Permission, Role, User


class SqlAlchemyPermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: str) -> Permission | None:
        result = await self._session.execute(select(Permission).where(Permission.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Permission]:
        result = await self._session.execute(select(Permission).order_by(Permission.code))
        return list(result.scalars().all())


class SqlAlchemyRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self._session.execute(select(Role).order_by(Role.name))
        return list(result.scalars().all())


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: uuid.UUID, *, include_deleted: bool = False
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        # Un usuario eliminado no puede autenticarse ni resolverse por email.
        result = await self._session.execute(
            select(User).where(
                func.lower(User.email) == email.lower(), User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, include_deleted: bool = False) -> list[User]:
        stmt = select(User)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await self._session.execute(stmt.order_by(User.full_name))
        return list(result.scalars().all())

    async def exists_email(self, email: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(func.lower(User.email) == email.lower(), User.deleted_at.is_(None))
        )
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def count_active_superusers(self, *, exclude_id: uuid.UUID | None = None) -> int:
        """Cuenta superusuarios vivos y activos (para no dejar el tenant sin admin)."""
        stmt = (
            select(func.count())
            .select_from(User)
            .join(Role, User.role_id == Role.id)
            .where(
                Role.slug == "superusuario",
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user
