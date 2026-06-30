"""Resincroniza el RBAC de los tenants con la fuente de verdad del código.

Atajo de mantenimiento manual; la app ya reconcilia al arrancar (ver
``main._lifespan`` y ``users.application.role_sync``). Útil para forzar la
convergencia sin reiniciar el servicio. Idempotente.

Uso (desde ``backend/`` con el venv):
    ./.venv/Scripts/python.exe -m scripts.resync_roles            # todos los tenants
    ./.venv/Scripts/python.exe -m scripts.resync_roles <tenant_id>
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from sqlalchemy import text

from aurum.modules.users.application.role_sync import (
    ensure_permission_catalog,
    reconcile_all_tenants,
    sync_tenant_roles,
)
from aurum.shared.infrastructure.database import dispose_engine, get_session_factory


async def _resync_one(tenant_id: uuid.UUID) -> None:
    factory = get_session_factory()
    async with factory() as session:
        await ensure_permission_catalog(session)
        await session.commit()
    async with factory() as session:
        catalog = await ensure_permission_catalog(session)
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": str(tenant_id)},
        )
        roles = await sync_tenant_roles(session, tenant_id, catalog)
        await session.commit()
        print(f"  tenant {tenant_id}: {len(roles)} rol(es) asegurados.")


async def main(target: uuid.UUID | None) -> None:
    if target is not None:
        await _resync_one(target)
    else:
        tenants, touched = await reconcile_all_tenants(get_session_factory())
        print(f"Listo. {tenants} tenant(s), {touched} rol(es) asegurados.")
    await dispose_engine()


if __name__ == "__main__":
    arg = uuid.UUID(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(main(arg))
