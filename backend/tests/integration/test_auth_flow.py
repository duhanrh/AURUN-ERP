"""Pruebas de extremo a extremo de Fase 2: provisionamiento, login, RBAC y RLS.

Ejercitan la app real (ASGI en memoria) contra PostgreSQL con el rol de aplicación
(NOBYPASSRLS). Cada prueba provisiona su propio tenant con subdominio/emails únicos,
de modo que las aserciones por tenant son deterministas sin necesidad de limpieza.
Se omiten si no hay base de datos disponible.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from aurum.main import create_app
from aurum.shared.config import get_settings


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


async def _provision(client: AsyncClient, *, admin_password: str = "Admin-12345") -> dict:
    sub = _unique("acme")
    resp = await client.post(
        "/api/v1/platform/tenants",
        json={
            "name": "ACME Metales",
            "subdomain": sub,
            "admin_email": f"admin-{sub}@example.com",
            "admin_full_name": "Admin Minero",
            "admin_password": admin_password,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client: AsyncClient, tenant_id: str, email: str, password: str):
    return await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": password},
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_provisioning_seeds_six_base_roles(client: AsyncClient) -> None:
    data = await _provision(client)
    assert data["roles_created"] == 6
    assert data["initial_password"]
    assert uuid.UUID(data["tenant_id"])


async def test_login_and_me_returns_superuser_permissions(client: AsyncClient) -> None:
    tenant = await _provision(client)
    resp = await _login(client, tenant["tenant_id"], tenant["admin_email"], "Admin-12345")
    assert resp.status_code == 200, resp.text
    tokens = resp.json()

    me = await client.get("/api/v1/auth/me", headers=_bearer(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "superusuario"
    assert "users:manage" in body["permissions"]
    assert body["tenant_id"] == tenant["tenant_id"]


async def test_bad_credentials_are_rejected(client: AsyncClient) -> None:
    tenant = await _provision(client)
    resp = await _login(client, tenant["tenant_id"], tenant["admin_email"], "wrong-password")
    assert resp.status_code == 401


async def test_admin_can_create_user_and_list_roles(client: AsyncClient) -> None:
    tenant = await _provision(client)
    login = await _login(client, tenant["tenant_id"], tenant["admin_email"], "Admin-12345")
    admin_token = login.json()["access_token"]
    auth = _bearer(admin_token)

    roles = await client.get("/api/v1/roles", headers=auth)
    assert roles.status_code == 200
    slugs = {r["slug"] for r in roles.json()}
    assert {"superusuario", "operativo", "finanzas", "laboratorio", "solo_lectura"} <= slugs

    new_email = _unique("operario") + "@example.com"
    created = await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": new_email,
            "full_name": "Operario Uno",
            "password": "Operario-123",
            "role_slug": "operativo",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["role"]["slug"] == "operativo"

    listing = await client.get("/api/v1/users", headers=auth)
    assert listing.status_code == 200
    emails = {u["email"] for u in listing.json()}
    assert {tenant["admin_email"], new_email} <= emails


async def test_rbac_blocks_user_without_manage_permission(client: AsyncClient) -> None:
    tenant = await _provision(client)
    admin_login = await _login(client, tenant["tenant_id"], tenant["admin_email"], "Admin-12345")
    auth = _bearer(admin_login.json()["access_token"])

    op_email = _unique("op") + "@example.com"
    await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": op_email,
            "full_name": "Operario",
            "password": "Operario-123",
            "role_slug": "operativo",
        },
    )

    op_login = await _login(client, tenant["tenant_id"], op_email, "Operario-123")
    op_auth = _bearer(op_login.json()["access_token"])

    # El operativo no tiene users:manage => 403 al listar/crear usuarios.
    forbidden = await client.get("/api/v1/users", headers=op_auth)
    assert forbidden.status_code == 403


async def test_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)

    login_a = await _login(client, tenant_a["tenant_id"], tenant_a["admin_email"], "Admin-12345")
    auth_a = _bearer(login_a.json()["access_token"])

    # El admin de A solo ve a su propio admin, nunca a usuarios del tenant B.
    users_a = await client.get("/api/v1/users", headers=auth_a)
    assert users_a.status_code == 200
    emails_a = {u["email"] for u in users_a.json()}
    assert emails_a == {tenant_a["admin_email"]}
    assert tenant_b["admin_email"] not in emails_a


async def test_refresh_rotation_and_reuse_detection(client: AsyncClient) -> None:
    tenant = await _provision(client)
    headers = {"X-Tenant-ID": tenant["tenant_id"]}
    login = await _login(client, tenant["tenant_id"], tenant["admin_email"], "Admin-12345")
    first = login.json()["refresh_token"]

    rotated = await client.post(
        "/api/v1/auth/refresh", headers=headers, json={"refresh_token": first}
    )
    assert rotated.status_code == 200
    second = rotated.json()["refresh_token"]
    assert second != first

    # Reutilizar el refresh ya rotado debe rechazarse (detección de robo).
    reused = await client.post(
        "/api/v1/auth/refresh", headers=headers, json={"refresh_token": first}
    )
    assert reused.status_code == 401

    # Y la reutilización revoca toda la cadena: el token rotado tampoco sirve ya.
    after_breach = await client.post(
        "/api/v1/auth/refresh", headers=headers, json={"refresh_token": second}
    )
    assert after_breach.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    tenant = await _provision(client)
    login = await _login(client, tenant["tenant_id"], tenant["admin_email"], "Admin-12345")
    tokens = login.json()

    logout = await client.post(
        "/api/v1/auth/logout",
        headers=_bearer(tokens["access_token"]),
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 401


async def test_duplicate_subdomain_is_conflict(client: AsyncClient) -> None:
    tenant = await _provision(client)
    # Reusar el mismo subdominio debe dar 409.
    resp = await client.post(
        "/api/v1/platform/tenants",
        json={
            "name": "Duplicada",
            "subdomain": tenant["subdomain"],
            "admin_email": "otro@example.com",
            "admin_full_name": "Otro",
            "admin_password": "Otro-12345",
        },
    )
    assert resp.status_code == 409
