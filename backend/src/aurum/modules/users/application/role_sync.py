"""Reconciliación idempotente del RBAC: el código es la **única fuente de verdad**.

El catálogo de permisos y los roles base se versionan en código
(``users/domain/permissions.py``, sección 10.3). La base de datos debe **converger**
a esas definiciones, no mantener una foto del momento del provisionamiento. Aquí vive
la única implementación de "asegurar que un tenant tenga el catálogo y sus roles base
con los permisos que define el código", reutilizada por:

- el **provisionamiento** de un tenant nuevo (crea catálogo + roles + admin),
- el **arranque de la app** (reconcilia todos los tenants existentes),
- el script de mantenimiento ``scripts/resync_roles.py``.

Es estrictamente **aditivo** (no borra roles ni revoca permisos) e idempotente:
ejecutarlo dos veces no cambia nada la segunda vez.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aurum.modules.tenants.infrastructure.models import Tenant
from aurum.modules.users.domain.permissions import BASE_ROLES, PERMISSION_CATALOG, RoleDef
from aurum.modules.users.infrastructure.models import Permission, Role, RolePermission

logger = logging.getLogger("aurum.role_sync")


async def ensure_permission_catalog(session: AsyncSession) -> dict[str, Permission]:
    """Upsert idempotente del catálogo de plataforma (tabla ``permissions``, sin RLS)."""
    result = await session.execute(select(Permission))
    by_code = {p.code: p for p in result.scalars().all()}
    for definition in PERMISSION_CATALOG:
        existing = by_code.get(definition.code)
        if existing is None:
            perm = Permission(
                code=definition.code,
                resource=definition.resource,
                action=definition.action,
                description=definition.description,
            )
            session.add(perm)
            by_code[definition.code] = perm
        elif existing.description != definition.description:
            existing.description = definition.description  # mantener metadatos al día
    await session.flush()
    return by_code


def _desired_codes(definition: RoleDef, catalog: dict[str, Permission]) -> set[str]:
    return set(catalog) if definition.grants_all else {p.code for p in definition.permissions}


async def sync_tenant_roles(
    session: AsyncSession, tenant_id: uuid.UUID, catalog: dict[str, Permission]
) -> dict[str, Role]:
    """Asegura los roles base del tenant y sus permisos según el código (aditivo).

    Crea los roles base que falten y añade los permisos que falten a cada uno.
    Requiere que el contexto RLS (``app.current_tenant_id``) ya esté fijado al tenant.
    Devuelve los roles por ``slug`` (para que el provisionamiento enganche el admin).
    """
    existing = (await session.execute(select(Role))).scalars().all()
    roles_by_slug = {r.slug: r for r in existing}

    for definition in BASE_ROLES:
        role = roles_by_slug.get(definition.slug)
        if role is None:
            role = Role(
                tenant_id=tenant_id,
                slug=definition.slug,
                name=definition.name,
                description=definition.description,
                is_system=True,
            )
            session.add(role)
            roles_by_slug[definition.slug] = role

        current_ids = {link.permission_id for link in role.permission_links}
        for code in _desired_codes(definition, catalog):
            perm = catalog.get(code)
            if perm is not None and perm.id not in current_ids:
                role.permission_links.append(
                    RolePermission(tenant_id=tenant_id, permission_id=perm.id)
                )
                current_ids.add(perm.id)

    await session.flush()
    return roles_by_slug


async def _set_tenant_scope(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def reconcile_all_tenants(factory: async_sessionmaker[AsyncSession]) -> tuple[int, int]:
    """Reconcilia el RBAC de **todos** los tenants. Devuelve ``(tenants, roles_tocados)``.

    El catálogo se asegura una vez; luego cada tenant se procesa en su **propia
    transacción** (el ``WITH CHECK`` de RLS de ``role_permissions`` exige que el
    ``app.current_tenant_id`` coincida con las filas que se insertan).
    """
    async with factory() as session:
        await ensure_permission_catalog(session)
        await session.commit()

    async with factory() as session:
        tenant_ids = list((await session.execute(select(Tenant.id))).scalars().all())

    touched = 0
    for tid in tenant_ids:
        async with factory() as session:
            # El catálogo ya está confirmado: aquí sólo se relee, ligado a esta sesión.
            catalog = await ensure_permission_catalog(session)
            await _set_tenant_scope(session, tid)
            roles = await sync_tenant_roles(session, tid, catalog)
            touched += len(roles)
            await session.commit()
    return len(tenant_ids), touched
