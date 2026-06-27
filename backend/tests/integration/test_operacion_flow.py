"""Pruebas E2E de Fase 4: Inventario, Compras y Ventas (criterios de aceptación).

Verifican que: (1) una OC aprobada genera un lote de inventario; (2) una OV no puede
exceder el stock disponible y lo consume al vender; (3) los KPIs reflejan datos
reales calculados. Contra PostgreSQL real con el rol de aplicación (NOBYPASSRLS).
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
    assert resp.status_code == 200, resp.text
    materials = resp.json()
    assert materials, "el provisionamiento debe sembrar el catálogo de materiales"
    return materials[0]


async def _create_supplier(client: AsyncClient, auth: dict) -> dict:
    resp = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Proveedor Test", "tax_id": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_customer(client: AsyncClient, auth: dict) -> dict:
    resp = await client.post(
        "/api/v1/customers",
        headers=auth,
        json={"legal_name": "Cliente Test", "tax_id": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_provisioning_seeds_material_catalog(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    resp = await client.get("/api/v1/inventory/materials", headers=auth)
    assert resp.status_code == 200
    codes = {m["code"] for m in resp.json()}
    assert {"AU24", "AG999", "PT", "PD"} <= codes


async def test_manual_lot_valuation(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)

    resp = await client.post(
        "/api/v1/inventory/lots",
        headers=auth,
        json={
            "material_id": material["id"],
            "form": "raw",
            "declared_purity": "0.9999",
            "gross_weight_g": "31.1034768",  # exactamente 1 oz troy
            "price_per_oz": "3000.00",
        },
    )
    assert resp.status_code == 201, resp.text
    lot = resp.json()
    # 1 oz fina × $3000 × 0.9999 ≈ $2999.70
    assert abs(float(lot["value_usd"]) - 2999.70) < 0.05
    assert lot["available_weight_g"] == "31.1034768"


async def test_approving_purchase_order_creates_lot(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    supplier = await _create_supplier(client, auth)

    created = await client.post(
        "/api/v1/purchasing/orders",
        headers=auth,
        json={
            "supplier_id": supplier["id"],
            "material_id": material["id"],
            "quantity_g": "1000",
            "declared_purity": "0.75",
            "price_per_oz": "2450",
            "form": "raw",
        },
    )
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["status"] == "pending_approval"
    assert order["lot_id"] is None

    # Antes de aprobar no hay lotes.
    lots_before = await client.get("/api/v1/inventory/lots", headers=auth)
    assert len(lots_before.json()) == 0

    approved = await client.post(
        f"/api/v1/purchasing/orders/{order['id']}/approve", headers=auth
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    lot_id = approved.json()["lot_id"]
    assert lot_id is not None

    # El lote existe con el peso de la OC y enlaza de vuelta a la orden.
    lots_after = await client.get("/api/v1/inventory/lots", headers=auth)
    assert len(lots_after.json()) == 1
    lot = lots_after.json()[0]
    assert lot["id"] == lot_id
    assert lot["available_weight_g"] == "1000.0000"
    assert lot["supplier_id"] == supplier["id"]

    # Re-aprobar una OC ya aprobada es conflicto.
    again = await client.post(f"/api/v1/purchasing/orders/{order['id']}/approve", headers=auth)
    assert again.status_code == 409


async def test_sale_consumes_stock_and_cannot_exceed(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    customer = await _create_customer(client, auth)

    lot_resp = await client.post(
        "/api/v1/inventory/lots",
        headers=auth,
        json={
            "material_id": material["id"],
            "form": "refined",
            "declared_purity": "0.999",
            "gross_weight_g": "500",
            "price_per_oz": "3100",
        },
    )
    lot = lot_resp.json()

    # Vender más de lo disponible → 409 stock insuficiente.
    over = await client.post(
        "/api/v1/sales/orders",
        headers=auth,
        json={
            "customer_id": customer["id"],
            "lot_id": lot["id"],
            "quantity_g": "600",
            "price_per_oz": "3200",
        },
    )
    assert over.status_code == 409, over.text
    assert over.json()["error"] == "insufficient_stock"

    # Vender una parte válida descuenta el stock.
    sale = await client.post(
        "/api/v1/sales/orders",
        headers=auth,
        json={
            "customer_id": customer["id"],
            "lot_id": lot["id"],
            "quantity_g": "200",
            "price_per_oz": "3200",
        },
    )
    assert sale.status_code == 201, sale.text
    sale_body = sale.json()
    assert sale_body["lot_code"] == lot["lot_code"]

    lot_after = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_after.json()["available_weight_g"] == "300.0000"

    # Cancelar la venta restituye el stock.
    cancelled = await client.patch(
        f"/api/v1/sales/orders/{sale_body['id']}/status",
        headers=auth,
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200, cancelled.text
    lot_restored = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_restored.json()["available_weight_g"] == "500.0000"


async def test_kpis_reflect_real_data(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    supplier = await _create_supplier(client, auth)

    # Inventario vacío.
    inv0 = await client.get("/api/v1/inventory/kpis", headers=auth)
    assert inv0.json()["total_lots"] == 0
    assert float(inv0.json()["total_value_usd"]) == 0.0

    # Crear OC y aprobarla → un lote, KPIs de compras e inventario suben.
    order = await client.post(
        "/api/v1/purchasing/orders",
        headers=auth,
        json={
            "supplier_id": supplier["id"],
            "material_id": material["id"],
            "quantity_g": "1000",
            "declared_purity": "0.75",
            "price_per_oz": "2450",
        },
    )
    pur_kpis = await client.get("/api/v1/purchasing/kpis", headers=auth)
    assert pur_kpis.json()["total_orders"] == 1
    assert pur_kpis.json()["pending_approval"] == 1
    assert float(pur_kpis.json()["total_amount_usd"]) > 0

    await client.post(f"/api/v1/purchasing/orders/{order.json()['id']}/approve", headers=auth)

    inv1 = await client.get("/api/v1/inventory/kpis", headers=auth)
    assert inv1.json()["total_lots"] == 1
    assert float(inv1.json()["total_value_usd"]) > 0

    pur_kpis2 = await client.get("/api/v1/purchasing/kpis", headers=auth)
    assert pur_kpis2.json()["approved"] == 1
    assert pur_kpis2.json()["pending_approval"] == 0


async def test_rbac_and_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)
    auth_a = await _admin_auth(client, tenant_a)
    auth_b = await _admin_auth(client, tenant_b)

    material_a = await _first_material(client, auth_a)
    await client.post(
        "/api/v1/inventory/lots",
        headers=auth_a,
        json={
            "material_id": material_a["id"],
            "form": "raw",
            "declared_purity": "0.9",
            "gross_weight_g": "100",
            "price_per_oz": "2000",
        },
    )

    # El tenant B no ve los lotes de A (RLS).
    lots_b = await client.get("/api/v1/inventory/lots", headers=auth_b)
    assert lots_b.status_code == 200
    assert lots_b.json() == []

    # Un rol sin sales:manage no puede crear OV, pero sí leer.
    reader_email = _unique("lector") + "@example.com"
    await client.post(
        "/api/v1/users",
        headers=auth_a,
        json={
            "email": reader_email,
            "full_name": "Lector",
            "password": "Lector-123",
            "role_slug": "solo_lectura",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_a["tenant_id"]},
        json={"email": reader_email, "password": "Lector-123"},
    )
    reader_auth = _bearer(login.json()["access_token"])

    assert (await client.get("/api/v1/inventory/lots", headers=reader_auth)).status_code == 200
    forbidden = await client.post(
        "/api/v1/inventory/lots",
        headers=reader_auth,
        json={
            "material_id": material_a["id"],
            "form": "raw",
            "declared_purity": "0.9",
            "gross_weight_g": "10",
            "price_per_oz": "2000",
        },
    )
    assert forbidden.status_code == 403
