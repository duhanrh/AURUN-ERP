"""Pruebas E2E de Fase 7 — Dashboard: KPIs reales, alertas y ticker (sección 7.16).

Verifican que el resumen agrega datos reales (inventario, ventas, compras,
contabilidad), que las alertas se derivan de reglas (stock crítico vs parámetro,
OC pendientes) y que el ticker de precios spot degrada de forma controlada
(``stale=True``) sin romper el Dashboard.
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


async def _first_material(client: AsyncClient, auth: dict) -> dict:
    resp = await client.get("/api/v1/inventory/materials", headers=auth)
    return resp.json()[0]


async def test_empty_dashboard_has_spot_ticker(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    summary = await client.get("/api/v1/dashboard/summary", headers=auth)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["kpis"]["total_lots"] == 0
    # El ticker siempre responde (degradación controlada).
    symbols = {p["symbol"] for p in body["spot_prices"]}
    assert {"XAU", "XAG", "XPT", "XPD"} == symbols
    assert all(p["stale"] for p in body["spot_prices"])


async def test_dashboard_aggregates_real_data_and_alerts(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)

    customer = await client.post(
        "/api/v1/customers",
        headers=auth,
        json={"legal_name": "Cliente DB", "tax_id": _unique("NIT")},
    )
    supplier = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Prov DB", "tax_id": _unique("NIT")},
    )

    # Lote pequeño (< stock mínimo 1000 g) → debe disparar alerta de stock crítico.
    lot = await client.post(
        "/api/v1/inventory/lots",
        headers=auth,
        json={
            "material_id": material["id"],
            "form": "refined",
            "declared_purity": "0.999",
            "gross_weight_g": "300",
            "price_per_oz": "3000",
        },
    )
    assert lot.status_code == 201, lot.text

    # OC pendiente de aprobación → KPI y alerta.
    await client.post(
        "/api/v1/purchasing/orders",
        headers=auth,
        json={
            "supplier_id": supplier.json()["id"],
            "material_id": material["id"],
            "quantity_g": "500",
            "declared_purity": "0.75",
            "price_per_oz": "2400",
        },
    )

    # Venta → genera ingreso y CxC.
    await client.post(
        "/api/v1/sales/orders",
        headers=auth,
        json={
            "customer_id": customer.json()["id"],
            "lot_id": lot.json()["id"],
            "quantity_g": "100",
            "price_per_oz": "3200",
        },
    )

    summary = (await client.get("/api/v1/dashboard/summary", headers=auth)).json()
    assert summary["kpis"]["total_lots"] == 1
    assert summary["kpis"]["purchases_pending"] == 1
    assert summary["kpis"]["sales_count"] == 1
    assert float(summary["kpis"]["sales_total_usd"]) > 0
    assert float(summary["kpis"]["receivable_usd"]) > 0

    categories = {a["category"] for a in summary["alerts"]}
    assert "stock" in categories  # stock crítico
    assert "purchasing" in categories  # OC pendiente

    # Stock por material marca el material vendido como crítico.
    critical_codes = {m["code"] for m in summary["material_stock"] if m["is_critical"]}
    assert material["code"] in critical_codes

    # Transacciones recientes incluyen la venta y la compra.
    kinds = {t["kind"] for t in summary["recent_transactions"]}
    assert {"sale", "purchase"} <= kinds


async def test_dashboard_requires_authentication(client: AsyncClient) -> None:
    tenant = await _provision(client)
    # Sin token de acceso, el guard de dashboard:access rechaza la petición.
    resp = await client.get(
        "/api/v1/dashboard/summary", headers={"X-Tenant-ID": tenant["tenant_id"]}
    )
    assert resp.status_code == 401
