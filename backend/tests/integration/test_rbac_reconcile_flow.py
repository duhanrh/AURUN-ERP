"""Pruebas E2E del reconciliador de RBAC: la BD converge a la fuente de verdad.

Verifican que: (1) un tenant provisionado obtiene el catálogo **completo** en su
superusuario (no una foto parcial); (2) si la BD deriva (faltan permisos de rol,
como en tenants viejos), la reconciliación los restaura; (3) es idempotente. Esto
garantiza que "lo del admin sin botones" no vuelva a pasar tras añadir permisos.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from aurum.main import create_app
from aurum.modules.users.application.role_sync import (
    ensure_permission_catalog,
    reconcile_all_tenants,
    sync_tenant_roles,
)
from aurum.modules.users.domain.permissions import PERMISSION_CATALOG
from aurum.shared.config import get_settings
from aurum.shared.infrastructure.database import get_session_factory

_CATALOG_SIZE = len(PERMISSION_CATALOG)


@pytest.fixture(scope="module", autouse=True)
async def _require_db() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(get_settings().database_url)
    try:
        conn = await engine.connect()
    except Exception:  # noqa: BLE001
        await engine.dispose()
        pytest.skip("PostgreSQL no disponible para pruebas de integración")
    else:
        await conn.close()
        await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def _provision(client: AsyncClient) -> dict:
    sub = _unique("acme")
    resp = await client.post(
        "/api/v1/platform/tenants",
        json={
            "name": "ACME Metales",
            "subdomain": sub,
            "admin_email": f"admin-{sub}@example.com",
            "admin_full_name": "Admin Minero",
            "admin_password": "Admin-12345",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _superuser_perm_count(tenant_id: str) -> int:
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": tenant_id},
        )
        row = await session.execute(
            text(
                "SELECT count(*) FROM role_permissions rp "
                "JOIN roles r ON r.id = rp.role_id WHERE r.slug = 'superusuario'"
            )
        )
        return int(row.scalar_one())


async def test_provisioning_grants_full_catalog(client: AsyncClient) -> None:
    tenant = await _provision(client)
    # El superusuario nace con TODO el catálogo (no una foto parcial).
    assert await _superuser_perm_count(tenant["tenant_id"]) == _CATALOG_SIZE

    # Y el login refleja esos permisos de gestión (acciones disponibles).
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": tenant["admin_email"], "password": "Admin-12345"},
    )
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    perms = set(me.json()["permissions"])
    assert {"inventory:manage", "purchasing:manage", "sales:manage"} <= perms


async def test_reconcile_restores_drifted_permissions(client: AsyncClient) -> None:
    tenant = await _provision(client)
    tid = tenant["tenant_id"]
    assert await _superuser_perm_count(tid) == _CATALOG_SIZE

    # Simula la deriva de un tenant "viejo": se le quitan permisos al superusuario.
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": tid},
        )
        await session.execute(
            text(
                "DELETE FROM role_permissions rp USING roles r "
                "WHERE rp.role_id = r.id AND r.slug = 'superusuario' "
                "AND rp.ctid IN (SELECT rp2.ctid FROM role_permissions rp2 "
                "JOIN roles r2 ON r2.id = rp2.role_id WHERE r2.slug='superusuario' LIMIT 5)"
            )
        )
        await session.commit()
    assert await _superuser_perm_count(tid) == _CATALOG_SIZE - 5

    # Reconciliar (lo que hace la app al arrancar) restaura la convergencia…
    async with factory() as session:
        catalog = await ensure_permission_catalog(session)
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": tid},
        )
        await sync_tenant_roles(session, uuid.UUID(tid), catalog)
        await session.commit()
    assert await _superuser_perm_count(tid) == _CATALOG_SIZE

    # …y es idempotente: una segunda pasada no cambia nada.
    await reconcile_all_tenants(get_session_factory())
    assert await _superuser_perm_count(tid) == _CATALOG_SIZE
