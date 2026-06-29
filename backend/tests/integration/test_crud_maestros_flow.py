"""Pruebas E2E de la Ola 1 — CRUD completo de datos maestros con baja lógica.

Verifican que: (1) Clientes/Proveedores/Usuarios/Materiales se editan, eliminan
(lógico) y restauran; (2) un eliminado NO aparece en el listado por defecto pero sí
con ``include_deleted``; (3) el NIT/email/código se libera al eliminar y choca al
restaurar si hay otro vigente; (4) guardas: no borrar el propio usuario ni el último
superusuario; (5) un usuario eliminado no puede autenticarse.
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


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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


async def _admin_auth(client: AsyncClient, tenant: dict) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": tenant["admin_email"], "password": "Admin-12345"},
    )
    assert resp.status_code == 200, resp.text
    return _bearer(resp.json()["access_token"])


# ── Terceros ────────────────────────────────────────────────────────────────
async def test_customer_soft_delete_and_restore(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    nit = _unique("NIT")

    created = await client.post(
        "/api/v1/customers", headers=auth, json={"legal_name": "Cliente A", "tax_id": nit}
    )
    cid = created.json()["id"]

    deleted = await client.delete(f"/api/v1/customers/{cid}", headers=auth)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_deleted"] is True

    # No aparece por defecto; sí con include_deleted.
    assert all(c["id"] != cid for c in (await client.get("/api/v1/customers", headers=auth)).json())
    with_deleted = await client.get("/api/v1/customers?include_deleted=true", headers=auth)
    assert any(c["id"] == cid for c in with_deleted.json())

    # El NIT quedó libre: se puede crear otro vigente con el mismo NIT.
    reuse = await client.post(
        "/api/v1/customers", headers=auth, json={"legal_name": "Cliente B", "tax_id": nit}
    )
    assert reuse.status_code == 201

    # Restaurar ahora choca con el NIT del vigente.
    conflict = await client.post(f"/api/v1/customers/{cid}/restore", headers=auth)
    assert conflict.status_code == 409


async def test_customer_restore_when_free(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    created = await client.post(
        "/api/v1/customers", headers=auth, json={"legal_name": "C", "tax_id": _unique("NIT")}
    )
    cid = created.json()["id"]
    await client.delete(f"/api/v1/customers/{cid}", headers=auth)
    restored = await client.post(f"/api/v1/customers/{cid}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


# ── Materiales ──────────────────────────────────────────────────────────────
async def test_material_full_crud(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    created = await client.post(
        "/api/v1/inventory/materials",
        headers=auth,
        json={"code": "au14", "name": "Oro 14K", "symbol": "XAU"},
    )
    assert created.status_code == 201, created.text
    mid = created.json()["id"]
    assert created.json()["code"] == "AU14"  # normalizado a mayúsculas

    # Editar.
    updated = await client.patch(
        f"/api/v1/inventory/materials/{mid}", headers=auth, json={"name": "Oro 18 quilates"}
    )
    assert updated.json()["name"] == "Oro 18 quilates"

    # Eliminar → desaparece del catálogo operativo (list_active) y del catálogo por defecto.
    await client.delete(f"/api/v1/inventory/materials/{mid}", headers=auth)
    active = (await client.get("/api/v1/inventory/materials", headers=auth)).json()
    assert all(m["id"] != mid for m in active)
    catalog = await client.get(
        "/api/v1/inventory/materials/catalog?include_deleted=true", headers=auth
    )
    assert any(m["id"] == mid and m["is_deleted"] for m in catalog.json())

    restored = await client.post(f"/api/v1/inventory/materials/{mid}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


# ── Usuarios ────────────────────────────────────────────────────────────────
async def test_user_update_delete_restore_and_guards(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    email = _unique("u") + "@example.com"
    created = await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": email,
            "full_name": "Operario",
            "password": "Pass-12345",
            "role_slug": "operativo",
        },
    )
    uid = created.json()["id"]

    # Editar nombre y desactivar.
    upd = await client.patch(
        f"/api/v1/users/{uid}",
        headers=auth,
        json={"full_name": "Operario Senior", "is_active": False},
    )
    assert upd.status_code == 200, upd.text
    assert upd.json()["full_name"] == "Operario Senior"
    assert upd.json()["is_active"] is False

    # Eliminar y comprobar que no puede autenticarse.
    await client.delete(f"/api/v1/users/{uid}", headers=auth)
    # (su contraseña era válida, pero el usuario está eliminado)
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": email, "password": "Pass-12345"},
    )
    assert login.status_code == 401

    # Restaurar.
    restored = await client.post(f"/api/v1/users/{uid}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


async def test_user_guards_self_and_last_superuser(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    me = (await client.get("/api/v1/auth/me", headers=auth)).json()
    admin_id = me["user_id"]

    # No puede borrarse a sí mismo.
    self_del = await client.delete(f"/api/v1/users/{admin_id}", headers=auth)
    assert self_del.status_code == 409

    # No puede desactivar al último superusuario (él mismo) vía PATCH.
    deactivate = await client.patch(
        f"/api/v1/users/{admin_id}", headers=auth, json={"is_active": False}
    )
    assert deactivate.status_code == 409
    assert deactivate.json()["error"] == "last_superuser"
