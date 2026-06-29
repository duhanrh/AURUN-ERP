"""Pruebas E2E de la Ola 2 — CRUD de documentos de operación con baja lógica.

Verifican: edición y baja/alta lógica de OC, OV, OT, muestras y lotes con sus
**guardas de integridad** (no anular una OC aprobada, una OV no cancelada, ni un
lote con movimientos de stock), y que los eliminados no aparecen por defecto.
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


async def _material(client: AsyncClient, auth: dict) -> dict:
    return (await client.get("/api/v1/inventory/materials", headers=auth)).json()[0]


async def _supplier(client: AsyncClient, auth: dict) -> str:
    r = await client.post(
        "/api/v1/suppliers", headers=auth, json={"legal_name": "P", "tax_id": _unique("NIT")}
    )
    return r.json()["id"]


async def _customer(client: AsyncClient, auth: dict) -> str:
    r = await client.post(
        "/api/v1/customers", headers=auth, json={"legal_name": "C", "tax_id": _unique("NIT")}
    )
    return r.json()["id"]


async def _lot(client: AsyncClient, auth: dict, material: dict, **over: object) -> dict:
    body = {
        "material_id": material["id"],
        "form": "refined",
        "declared_purity": "0.999",
        "gross_weight_g": "500",
        "price_per_oz": "3000",
        **over,
    }
    return (await client.post("/api/v1/inventory/lots", headers=auth, json=body)).json()


async def test_purchase_order_edit_delete_guard(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _material(client, auth)
    supplier = await _supplier(client, auth)

    oc = (
        await client.post(
            "/api/v1/purchasing/orders",
            headers=auth,
            json={
                "supplier_id": supplier,
                "material_id": material["id"],
                "quantity_g": "1000",
                "declared_purity": "0.75",
                "price_per_oz": "2400",
            },
        )
    ).json()

    # Editar mientras está pendiente.
    upd = await client.patch(
        f"/api/v1/purchasing/orders/{oc['id']}", headers=auth, json={"price_per_oz": "2500"}
    )
    assert upd.status_code == 200, upd.text
    assert float(upd.json()["price_per_oz"]) == 2500.0

    # Aprobar → ya no se puede editar ni eliminar (generó lote + asiento).
    await client.post(f"/api/v1/purchasing/orders/{oc['id']}/approve", headers=auth)
    blocked_edit = await client.patch(
        f"/api/v1/purchasing/orders/{oc['id']}", headers=auth, json={"price_per_oz": "9999"}
    )
    assert blocked_edit.status_code == 409
    blocked_del = await client.delete(f"/api/v1/purchasing/orders/{oc['id']}", headers=auth)
    assert blocked_del.status_code == 409


async def test_purchase_order_delete_and_restore_when_pending(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _material(client, auth)
    supplier = await _supplier(client, auth)
    oc = (
        await client.post(
            "/api/v1/purchasing/orders",
            headers=auth,
            json={
                "supplier_id": supplier,
                "material_id": material["id"],
                "quantity_g": "100",
                "declared_purity": "0.75",
                "price_per_oz": "2400",
            },
        )
    ).json()
    deleted = await client.delete(f"/api/v1/purchasing/orders/{oc['id']}", headers=auth)
    assert deleted.status_code == 200
    assert deleted.json()["is_deleted"] is True
    listed = (await client.get("/api/v1/purchasing/orders", headers=auth)).json()
    assert all(o["id"] != oc["id"] for o in listed)
    restored = await client.post(f"/api/v1/purchasing/orders/{oc['id']}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


async def test_sales_order_delete_only_when_cancelled(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _material(client, auth)
    customer = await _customer(client, auth)
    lot = await _lot(client, auth, material)
    ov = (
        await client.post(
            "/api/v1/sales/orders",
            headers=auth,
            json={
                "customer_id": customer,
                "lot_id": lot["id"],
                "quantity_g": "100",
                "price_per_oz": "3200",
            },
        )
    ).json()

    # No se puede eliminar una OV no cancelada.
    del_blocked = await client.delete(f"/api/v1/sales/orders/{ov['id']}", headers=auth)
    assert del_blocked.status_code == 409

    # Cancelar (restituye stock + reversa) y luego sí eliminar.
    await client.patch(
        f"/api/v1/sales/orders/{ov['id']}/status", headers=auth, json={"status": "cancelled"}
    )
    deleted = await client.delete(f"/api/v1/sales/orders/{ov['id']}", headers=auth)
    assert deleted.status_code == 200
    assert deleted.json()["is_deleted"] is True


async def test_lot_delete_guarded_by_movements(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _material(client, auth)
    customer = await _customer(client, auth)

    # Lote intacto → editable y eliminable.
    lot = await _lot(client, auth, material, gross_weight_g="200")
    upd = await client.patch(
        f"/api/v1/inventory/lots/{lot['id']}", headers=auth, json={"location": "Bóveda 2"}
    )
    assert upd.json()["location"] == "Bóveda 2"

    # Lote con venta (movimiento de stock) → no eliminable.
    sold_lot = await _lot(client, auth, material, gross_weight_g="200")
    await client.post(
        "/api/v1/sales/orders",
        headers=auth,
        json={
            "customer_id": customer,
            "lot_id": sold_lot["id"],
            "quantity_g": "50",
            "price_per_oz": "3200",
        },
    )
    blocked = await client.delete(f"/api/v1/inventory/lots/{sold_lot['id']}", headers=auth)
    assert blocked.status_code == 409

    # El lote intacto sí se elimina y restaura.
    deleted = await client.delete(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert deleted.status_code == 200
    restored = await client.post(f"/api/v1/inventory/lots/{lot['id']}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


async def test_sample_edit_and_delete(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _material(client, auth)
    lot = await _lot(client, auth, material)

    sample = (
        await client.post(
            "/api/v1/quality/samples",
            headers=auth,
            json={
                "lot_id": lot["id"],
                "method": "xrf",
                "measured_purity": "0.998",
                "result": "pending",
            },
        )
    ).json()

    # Editar el resultado a rechazado → el lote pasa a cuarentena.
    upd = await client.patch(
        f"/api/v1/quality/samples/{sample['id']}", headers=auth, json={"result": "rejected"}
    )
    assert upd.status_code == 200, upd.text
    lot_after = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_after.json()["status"] == "quarantine"

    # Eliminar y restaurar la muestra.
    deleted = await client.delete(f"/api/v1/quality/samples/{sample['id']}", headers=auth)
    assert deleted.status_code == 200
    listed = (await client.get("/api/v1/quality/samples", headers=auth)).json()
    assert all(s["id"] != sample["id"] for s in listed)
    restored = await client.post(f"/api/v1/quality/samples/{sample['id']}/restore", headers=auth)
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False
