"""Pruebas E2E de Fase 8 — API pública con API Keys y scopes (sección 7.19).

Verifican que: (1) un tenant crea una API Key con scopes y obtiene la clave una vez;
(2) la API pública (``/public/v1``) autentica por API Key, resuelve el tenant y
respeta RLS; (3) un scope faltante da 403; (4) una clave inválida/revocada da 401;
(5) la gestión de claves exige la sesión interactiva con permiso.
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


async def _create_key(client: AsyncClient, auth: dict, scopes: list[str]) -> str:
    resp = await client.post(
        "/api/v1/configuration/api-keys",
        headers=auth,
        json={"name": "Integración BI", "scopes": scopes},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["key"]["scopes"] == scopes
    assert body["full_key"].startswith("aurum_")
    return body["full_key"]


async def test_public_api_reads_with_api_key(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    full_key = await _create_key(client, auth, ["inventory:read"])

    # La API pública resuelve el tenant de la clave y devuelve sus materiales.
    materials = await client.get("/public/v1/inventory/materials", headers={"X-API-Key": full_key})
    assert materials.status_code == 200, materials.text
    codes = {m["code"] for m in materials.json()}
    assert {"AU24", "AG999"} <= codes

    lots = await client.get("/public/v1/inventory/lots", headers={"X-API-Key": full_key})
    assert lots.status_code == 200
    assert lots.json() == []  # tenant nuevo sin lotes


async def test_public_api_enforces_scopes(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    # Clave solo con inventory:read → no puede leer reportes.
    full_key = await _create_key(client, auth, ["inventory:read"])

    report = await client.get(
        "/public/v1/reports/operational_kpis", headers={"X-API-Key": full_key}
    )
    assert report.status_code == 403
    assert report.json()["error"] == "insufficient_scope"

    # Con el scope correcto sí.
    key2 = await _create_key(client, auth, ["reports:read"])
    ok = await client.get("/public/v1/reports/operational_kpis", headers={"X-API-Key": key2})
    assert ok.status_code == 200, ok.text
    assert ok.json()["title"] == "KPIs Operativos"


async def test_invalid_and_revoked_keys_rejected(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    # Sin cabecera → 401.
    no_key = await client.get("/public/v1/inventory/materials")
    assert no_key.status_code == 401

    # Clave con formato inválido → 401.
    bad = await client.get(
        "/public/v1/inventory/materials", headers={"X-API-Key": "no-es-una-clave"}
    )
    assert bad.status_code == 401

    # Revocar una clave la inhabilita.
    full_key = await _create_key(client, auth, ["inventory:read"])
    keys = (await client.get("/api/v1/configuration/api-keys", headers=auth)).json()
    key_id = keys[0]["id"]
    revoke = await client.delete(f"/api/v1/configuration/api-keys/{key_id}", headers=auth)
    assert revoke.status_code == 200
    assert revoke.json()["is_active"] is False

    after = await client.get("/public/v1/inventory/materials", headers={"X-API-Key": full_key})
    assert after.status_code == 401


async def test_api_key_management_requires_permission(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    reader_email = _unique("r") + "@example.com"
    await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": reader_email,
            "full_name": "Lector",
            "password": "Lector-123",
            "role_slug": "solo_lectura",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": reader_email, "password": "Lector-123"},
    )
    reader_auth = _bearer(login.json()["access_token"])
    forbidden = await client.post(
        "/api/v1/configuration/api-keys",
        headers=reader_auth,
        json={"name": "x", "scopes": ["inventory:read"]},
    )
    assert forbidden.status_code == 403
