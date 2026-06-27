"""Pruebas E2E de Fase 3: CRUD de Terceros (Clientes/Proveedores), RBAC y RLS.

Ejercitan la app real (ASGI en memoria) contra PostgreSQL con el rol de aplicación
(NOBYPASSRLS). Cada prueba provisiona su propio tenant para que las aserciones por
tenant sean deterministas. Se omiten si no hay base de datos disponible.
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


async def _create_user(
    client: AsyncClient, auth: dict, email: str, role_slug: str
) -> dict[str, str]:
    created = await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": email,
            "full_name": "Usuario Prueba",
            "password": "Usuario-123",
            "role_slug": role_slug,
        },
    )
    assert created.status_code == 201, created.text
    return created.json()


async def test_create_and_list_supplier(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    created = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={
            "legal_name": "Minera del Chocó S.A.S.",
            "tax_id": "901.234.567-1",
            "country": "CO",
            "city": "Chocó",
            "contact_name": "Andrés Ramírez",
            "email": "contacto@mineradelchoco.co",
            "main_material": "Oro Crudo",
            "certifications": "RUC, RUCOM",
            "rating": 4.6,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["kind"] == "supplier"
    assert body["rating"] == 4.6
    assert body["status"] == "active"

    listing = await client.get("/api/v1/suppliers", headers=auth)
    assert listing.status_code == 200
    names = {s["legal_name"] for s in listing.json()}
    assert "Minera del Chocó S.A.S." in names


async def test_create_customer_and_kpis(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    for status_value in ("active", "active", "evaluation", "inactive"):
        resp = await client.post(
            "/api/v1/customers",
            headers=auth,
            json={
                "legal_name": _unique("Cliente"),
                "tax_id": _unique("NIT"),
                "segment": "Joyería / Retail",
                "status": status_value,
                "credit_limit": 50000,
            },
        )
        assert resp.status_code == 201, resp.text

    kpis = await client.get("/api/v1/customers/kpis", headers=auth)
    assert kpis.status_code == 200
    data = kpis.json()
    assert data["total"] == 4
    assert data["active"] == 2
    assert data["evaluation"] == 1
    assert data["inactive"] == 1


async def test_update_party_and_inactivate(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    created = await client.post(
        "/api/v1/customers",
        headers=auth,
        json={"legal_name": "Joyería Oro & Arte", "tax_id": "811.223.456-7"},
    )
    party_id = created.json()["id"]

    patched = await client.patch(
        f"/api/v1/customers/{party_id}",
        headers=auth,
        json={"status": "inactive", "credit_limit": 30000},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "inactive"
    assert patched.json()["credit_limit"] == 30000.0
    # El nombre no enviado en el PATCH no se altera.
    assert patched.json()["legal_name"] == "Joyería Oro & Arte"


async def test_get_party_by_id_and_404(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    created = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Plata Andina", "tax_id": "890.445.221-3", "rating": 3.8},
    )
    party_id = created.json()["id"]

    fetched = await client.get(f"/api/v1/suppliers/{party_id}", headers=auth)
    assert fetched.status_code == 200
    assert fetched.json()["legal_name"] == "Plata Andina"

    missing = await client.get(f"/api/v1/suppliers/{uuid.uuid4()}", headers=auth)
    assert missing.status_code == 404


async def test_duplicate_tax_id_same_kind_is_conflict(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    payload = {"legal_name": "Proveedor A", "tax_id": "900.111.222-3"}
    first = await client.post("/api/v1/suppliers", headers=auth, json=payload)
    assert first.status_code == 201
    dup = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Proveedor B", "tax_id": "900.111.222-3"},
    )
    assert dup.status_code == 409


async def test_same_tax_id_across_kinds_is_allowed(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    tax_id = "860.005.235-2"
    sup = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Tercero Mixto", "tax_id": tax_id},
    )
    cus = await client.post(
        "/api/v1/customers",
        headers=auth,
        json={"legal_name": "Tercero Mixto", "tax_id": tax_id},
    )
    assert sup.status_code == 201
    assert cus.status_code == 201


async def test_read_only_role_cannot_write(client: AsyncClient) -> None:
    tenant = await _provision(client)
    admin_auth = await _admin_auth(client, tenant)

    email = _unique("lector") + "@example.com"
    await _create_user(client, admin_auth, email, "solo_lectura")
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": email, "password": "Usuario-123"},
    )
    reader_auth = _bearer(login.json()["access_token"])

    # solo_lectura tiene customers:access pero NO customers:manage.
    listing = await client.get("/api/v1/customers", headers=reader_auth)
    assert listing.status_code == 200

    forbidden = await client.post(
        "/api/v1/customers",
        headers=reader_auth,
        json={"legal_name": "No permitido", "tax_id": "123"},
    )
    assert forbidden.status_code == 403


async def test_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)
    auth_a = await _admin_auth(client, tenant_a)
    auth_b = await _admin_auth(client, tenant_b)

    await client.post(
        "/api/v1/suppliers",
        headers=auth_a,
        json={"legal_name": "Solo de A", "tax_id": _unique("NIT")},
    )

    suppliers_b = await client.get("/api/v1/suppliers", headers=auth_b)
    assert suppliers_b.status_code == 200
    assert all(s["legal_name"] != "Solo de A" for s in suppliers_b.json())
