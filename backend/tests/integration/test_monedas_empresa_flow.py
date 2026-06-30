"""Pruebas E2E de Monedas configurables y Datos de la Empresa (sección 7.17).

Verifican: (1) el tenant nace con el catálogo base de monedas y la base = parámetro
``base_currency``; (2) fijar otra moneda como base sincroniza el parámetro y deja una
sola base; (3) CRUD con baja lógica e invariantes (la base no se elimina); (4) los
datos de empresa se inicializan vacíos y se actualizan.
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


async def _auth(client: AsyncClient, tenant: dict) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": tenant["admin_email"], "password": "Admin-12345"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_tenant_seeded_with_currencies(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)
    resp = await client.get("/api/v1/configuration/currencies", headers=auth)
    assert resp.status_code == 200, resp.text
    by_code = {c["code"]: c for c in resp.json()}
    assert {"USD", "COP", "EUR"} <= set(by_code)
    assert by_code["USD"]["is_base"] is True  # base por defecto = parámetro base_currency
    assert by_code["COP"]["decimals"] == 0


async def test_set_base_syncs_parameter_and_is_unique(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)
    currencies = {
        c["code"]: c
        for c in (await client.get("/api/v1/configuration/currencies", headers=auth)).json()
    }
    cop_id = currencies["COP"]["id"]

    resp = await client.post(f"/api/v1/configuration/currencies/{cop_id}/set-base", headers=auth)
    assert resp.status_code == 200, resp.text

    after = {
        c["code"]: c
        for c in (await client.get("/api/v1/configuration/currencies", headers=auth)).json()
    }
    assert after["COP"]["is_base"] is True
    assert after["USD"]["is_base"] is False  # una sola base
    params = await client.get("/api/v1/configuration/parameters", headers=auth)
    assert params.json()["base_currency"] == "COP"  # parámetro legado sincronizado


async def test_currency_crud_and_base_protected(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)

    created = await client.post(
        "/api/v1/configuration/currencies",
        headers=auth,
        json={"code": "mxn", "name": "Peso mexicano", "symbol": "$", "decimals": 2},
    )
    assert created.status_code == 200, created.text
    assert created.json()["code"] == "MXN"  # normalizado a mayúsculas
    mxn_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/configuration/currencies/{mxn_id}", headers=auth)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_deleted"] is True

    # La moneda base no se puede eliminar.
    base = {
        c["code"]: c
        for c in (await client.get("/api/v1/configuration/currencies", headers=auth)).json()
    }["USD"]
    forbidden = await client.delete(f"/api/v1/configuration/currencies/{base['id']}", headers=auth)
    assert forbidden.status_code == 409, forbidden.text


async def test_company_initialized_empty_and_updates(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)

    initial = await client.get("/api/v1/configuration/company", headers=auth)
    assert initial.status_code == 200, initial.text
    assert initial.json()["legal_name"] == ""

    updated = await client.put(
        "/api/v1/configuration/company",
        headers=auth,
        json={
            "legal_name": "Compra de Oro y Platino S.A.S.",
            "tax_id": "900123456-7",
            "city": "Medellín",
            "phone": "3001234567",
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["legal_name"] == "Compra de Oro y Platino S.A.S."
    assert body["tax_id"] == "900123456-7"
    assert body["city"] == "Medellín"
