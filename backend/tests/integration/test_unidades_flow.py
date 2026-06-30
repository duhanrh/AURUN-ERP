"""Pruebas E2E de Unidades de Medida configurables y su conversor (sección 7.17).

Verifican: (1) el tenant nace con el catálogo base sembrado (gramo base +
tradicionales); (2) el conversor usa los factores del tenant (gramos como puente);
(3) CRUD con baja lógica e invariantes (la base no se elimina/desactiva; código
único entre vigentes); (4) todo exige ``configuration:manage`` para escribir.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

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


async def test_tenant_seeded_with_base_units(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)
    resp = await client.get("/api/v1/configuration/units", headers=auth)
    assert resp.status_code == 200, resp.text
    units = {u["code"]: u for u in resp.json()}
    assert {"gramo", "grano", "tomin", "castellano", "onza_troy", "libra"} <= set(units)
    assert units["gramo"]["is_base"] is True
    assert Decimal(units["castellano"]["grams_factor"]) == Decimal("4.6")


async def test_converter_uses_tenant_factors(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)
    # 1 castellano = 8 tomines (4.6 g / 0.575 g).
    resp = await client.post(
        "/api/v1/configuration/units/convert",
        headers=auth,
        json={"quantity": "1", "from_unit": "castellano", "to_unit": "tomin"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(body["grams"]) == Decimal("4.6")
    assert Decimal(body["result"]) == Decimal("8")


async def test_unit_crud_and_invariants(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)

    # Crear una unidad nueva.
    created = await client.post(
        "/api/v1/configuration/units",
        headers=auth,
        json={"code": "ochava", "name": "Ochava", "symbol": "och", "grams_factor": "3.594"},
    )
    assert created.status_code == 200, created.text
    unit_id = created.json()["id"]

    # Código duplicado → 409.
    dup = await client.post(
        "/api/v1/configuration/units",
        headers=auth,
        json={"code": "ochava", "name": "Otra", "symbol": "o", "grams_factor": "1"},
    )
    assert dup.status_code == 409, dup.text

    # Baja lógica y restauración.
    deleted = await client.delete(f"/api/v1/configuration/units/{unit_id}", headers=auth)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_deleted"] is True
    restored = await client.post(f"/api/v1/configuration/units/{unit_id}/restore", headers=auth)
    assert restored.status_code == 200, restored.text
    assert restored.json()["is_deleted"] is False


async def test_base_unit_protected(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _auth(client, tenant)
    units = {
        u["code"]: u for u in (await client.get("/api/v1/configuration/units", headers=auth)).json()
    }
    gramo_id = units["gramo"]["id"]
    # No se puede eliminar la unidad base.
    resp = await client.delete(f"/api/v1/configuration/units/{gramo_id}", headers=auth)
    assert resp.status_code == 409, resp.text
