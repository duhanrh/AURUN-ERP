"""Pruebas E2E de Fase 7 — Configuración: marca, parámetros y módulos (sección 7.17).

Verifican que: (1) un tenant nace con el tema por defecto (is_customized=false) y
parámetros/módulos sembrados; (2) la marca personalizada persiste en BD (no en
localStorage) y marca is_customized=true; (3) los parámetros y módulos se editan;
(4) la marca es legible por cualquier usuario autenticado pero solo editable con
configuration:manage; (5) aislamiento cross-tenant.
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


async def test_new_tenant_starts_with_default_theme(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    branding = await client.get("/api/v1/configuration/branding", headers=auth)
    assert branding.status_code == 200, branding.text
    assert branding.json()["is_customized"] is False
    assert branding.json()["color_primary"] is None

    params = await client.get("/api/v1/configuration/parameters", headers=auth)
    assert params.status_code == 200
    assert params.json()["base_currency"] == "USD"
    assert float(params.json()["min_stock_g"]) == 1000.0

    modules = await client.get("/api/v1/configuration/modules", headers=auth)
    assert modules.status_code == 200
    keys = {m["key"] for m in modules.json()}
    assert {"inventario", "finanzas", "reportes"} <= keys
    assert all(m["is_active"] for m in modules.json())


async def test_branding_persists_and_marks_customized(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    updated = await client.put(
        "/api/v1/configuration/branding",
        headers=auth,
        json={
            "brand_name": "Oro Andino",
            "tagline": "Refinación de precisión",
            "color_primary": "#3DAA6E",
            "color_background": "#0A0E0C",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["is_customized"] is True
    assert updated.json()["color_primary"] == "#3DAA6E"

    # Persistencia: una nueva sesión/petición ve el mismo branding (no localStorage).
    auth2 = await _admin_auth(client, tenant)
    again = await client.get("/api/v1/configuration/branding", headers=auth2)
    assert again.json()["brand_name"] == "Oro Andino"
    assert again.json()["is_customized"] is True

    # Reset vuelve al tema por defecto.
    reset = await client.delete("/api/v1/configuration/branding", headers=auth)
    assert reset.status_code == 200
    assert reset.json()["is_customized"] is False
    assert reset.json()["brand_name"] is None


async def test_parameters_and_modules_can_be_edited(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    put = await client.put(
        "/api/v1/configuration/parameters",
        headers=auth,
        json={
            "base_currency": "COP",
            "weight_unit": "kg",
            "min_stock_g": "500",
            "min_margin_pct": "8.5",
            "language": "es",
            "timezone": "America/Bogota",
            "date_format": "DD/MM/YYYY",
            "regulatory_entity": "ANM",
        },
    )
    assert put.status_code == 200, put.text
    assert put.json()["base_currency"] == "COP"
    assert float(put.json()["min_margin_pct"]) == 8.5

    toggled = await client.put(
        "/api/v1/configuration/modules/reportes",
        headers=auth,
        json={"is_active": False},
    )
    assert toggled.status_code == 200, toggled.text
    assert toggled.json()["is_active"] is False

    modules = await client.get("/api/v1/configuration/modules", headers=auth)
    reportes = next(m for m in modules.json() if m["key"] == "reportes")
    assert reportes["is_active"] is False

    # Módulo inexistente → 404.
    missing = await client.put(
        "/api/v1/configuration/modules/inexistente", headers=auth, json={"is_active": True}
    )
    assert missing.status_code == 404


async def test_branding_readable_but_write_requires_manage(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    reader_email = _unique("lector") + "@example.com"
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

    # Solo lectura puede leer la marca (para aplicar el tema)...
    assert (
        await client.get("/api/v1/configuration/branding", headers=reader_auth)
    ).status_code == 200
    # ...pero no editarla.
    forbidden = await client.put(
        "/api/v1/configuration/branding", headers=reader_auth, json={"brand_name": "Hack"}
    )
    assert forbidden.status_code == 403

    # Lista de módulos: legible por cualquier autenticado (el sidebar la necesita)…
    modules = await client.get("/api/v1/configuration/modules", headers=reader_auth)
    assert modules.status_code == 200
    assert any(m["key"] == "inventario" for m in modules.json())
    # …pero activar/desactivar sigue exigiendo configuration:manage.
    toggle = await client.put(
        "/api/v1/configuration/modules/reportes",
        headers=reader_auth,
        json={"is_active": False},
    )
    assert toggle.status_code == 403


async def test_config_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)
    auth_a = await _admin_auth(client, tenant_a)
    auth_b = await _admin_auth(client, tenant_b)

    await client.put(
        "/api/v1/configuration/branding",
        headers=auth_a,
        json={"brand_name": "Marca A", "color_primary": "#C9A84C"},
    )
    # El tenant B conserva su propia marca por defecto.
    branding_b = await client.get("/api/v1/configuration/branding", headers=auth_b)
    assert branding_b.json()["brand_name"] is None
    assert branding_b.json()["is_customized"] is False
