"""Pruebas E2E de Fase 5: Transformación y Calidad (criterios de aceptación).

Verifican que: (1) completar una OT consume el lote de entrada y crea el de salida
con el rendimiento; (2) una muestra de laboratorio "Rechazado" pone el lote en
cuarentena y bloquea el avance/cierre en el pipeline; (3) los KPIs son reales.
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


async def _materials(client: AsyncClient, auth: dict) -> list[dict]:
    resp = await client.get("/api/v1/inventory/materials", headers=auth)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _make_lot(
    client: AsyncClient, auth: dict, material_id: str, *, weight: str = "1000"
) -> dict:
    resp = await client.post(
        "/api/v1/inventory/lots",
        headers=auth,
        json={
            "material_id": material_id,
            "form": "raw",
            "declared_purity": "0.75",
            "gross_weight_g": weight,
            "price_per_oz": "2450",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_completing_transformation_consumes_input_and_creates_output(
    client: AsyncClient,
) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    materials = await _materials(client, auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    au24 = next(m for m in materials if m["code"] == "AU24")
    lot = await _make_lot(client, auth, au18["id"], weight="1000")

    created = await client.post(
        "/api/v1/transformation/orders",
        headers=auth,
        json={
            "input_lot_id": lot["id"],
            "process": "acid_refining",
            "input_quantity_g": "400",
            "yield_fraction": "0.95",
            "output_material_id": au24["id"],
            "output_purity": "0.9999",
            "output_form": "refined",
            "responsible": "Planta",
        },
    )
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["stage"] == "reception"
    assert order["status"] == "in_progress"
    assert order["expected_output_g"] == "380.0000"  # 400 × 0.95

    # Antes de completar: stock del lote de entrada intacto, sin lote de salida.
    lot_before = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_before.json()["available_weight_g"] == "1000.0000"

    completed = await client.post(
        f"/api/v1/transformation/orders/{order['id']}/complete", headers=auth
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["stage"] == "certified"
    output_lot_id = completed.json()["output_lot_id"]
    assert output_lot_id is not None

    # El lote de entrada bajó 400 g; el de salida existe con 380 g del material destino.
    lot_after = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_after.json()["available_weight_g"] == "600.0000"
    out = await client.get(f"/api/v1/inventory/lots/{output_lot_id}", headers=auth)
    assert out.json()["available_weight_g"] == "380.0000"
    assert out.json()["material_code"] == "AU24"


async def test_rejected_sample_quarantines_lot_and_blocks_pipeline(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    materials = await _materials(client, auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    au24 = next(m for m in materials if m["code"] == "AU24")
    lot = await _make_lot(client, auth, au18["id"])

    order = await client.post(
        "/api/v1/transformation/orders",
        headers=auth,
        json={
            "input_lot_id": lot["id"],
            "process": "acid_refining",
            "input_quantity_g": "400",
            "yield_fraction": "0.95",
            "output_material_id": au24["id"],
            "output_purity": "0.9999",
        },
    )
    order_id = order.json()["id"]

    # Muestra de lab rechazada → lote a cuarentena.
    sample = await client.post(
        "/api/v1/quality/samples",
        headers=auth,
        json={
            "lot_id": lot["id"],
            "method": "fire_assay",
            "measured_purity": "0.60",
            "result": "rejected",
            "analyst": "Lab",
        },
    )
    assert sample.status_code == 201, sample.text
    assert sample.json()["result"] == "rejected"
    # Diferencia = medida − declarada = 0.60 − 0.75 = −0.15.
    assert sample.json()["difference"] == "-0.15000"

    lot_q = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert lot_q.json()["status"] == "quarantine"

    # El pipeline no puede avanzar ni completarse con el lote en cuarentena.
    blocked_advance = await client.post(
        f"/api/v1/transformation/orders/{order_id}/advance", headers=auth
    )
    assert blocked_advance.status_code == 409
    assert blocked_advance.json()["error"] == "pipeline_blocked"

    blocked_complete = await client.post(
        f"/api/v1/transformation/orders/{order_id}/complete", headers=auth
    )
    assert blocked_complete.status_code == 409

    # La OT se ve como bloqueada.
    view = await client.get(f"/api/v1/transformation/orders/{order_id}", headers=auth)
    assert view.json()["blocked"] is True


async def test_approved_sample_lifts_quarantine_and_unblocks(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    materials = await _materials(client, auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    lot = await _make_lot(client, auth, au18["id"])

    await client.post(
        "/api/v1/quality/samples",
        headers=auth,
        json={
            "lot_id": lot["id"],
            "method": "xrf",
            "measured_purity": "0.50",
            "result": "rejected",
        },
    )
    q = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert q.json()["status"] == "quarantine"

    # Una muestra aprobada posterior levanta la cuarentena.
    await client.post(
        "/api/v1/quality/samples",
        headers=auth,
        json={
            "lot_id": lot["id"],
            "method": "xrf",
            "measured_purity": "0.76",
            "result": "approved",
        },
    )
    a = await client.get(f"/api/v1/inventory/lots/{lot['id']}", headers=auth)
    assert a.json()["status"] == "available"


async def test_advance_walks_the_pipeline_stages(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    materials = await _materials(client, auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    au24 = next(m for m in materials if m["code"] == "AU24")
    lot = await _make_lot(client, auth, au18["id"])

    order = await client.post(
        "/api/v1/transformation/orders",
        headers=auth,
        json={
            "input_lot_id": lot["id"],
            "process": "melting_alloy",
            "input_quantity_g": "100",
            "yield_fraction": "0.9",
            "output_material_id": au24["id"],
            "output_purity": "0.999",
        },
    )
    order_id = order.json()["id"]

    for expected in ("analysis", "melting", "refining", "certified"):
        resp = await client.post(f"/api/v1/transformation/orders/{order_id}/advance", headers=auth)
        assert resp.status_code == 200, resp.text
        assert resp.json()["stage"] == expected

    # En la última etapa no se puede avanzar más.
    overshoot = await client.post(f"/api/v1/transformation/orders/{order_id}/advance", headers=auth)
    assert overshoot.status_code == 409


async def test_kpis_reflect_real_data(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    materials = await _materials(client, auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    au24 = next(m for m in materials if m["code"] == "AU24")
    lot = await _make_lot(client, auth, au18["id"])

    await client.post(
        "/api/v1/transformation/orders",
        headers=auth,
        json={
            "input_lot_id": lot["id"],
            "process": "rolling",
            "input_quantity_g": "100",
            "yield_fraction": "0.9",
            "output_material_id": au24["id"],
            "output_purity": "0.999",
        },
    )
    t_kpis = await client.get("/api/v1/transformation/kpis", headers=auth)
    assert t_kpis.json()["total_orders"] == 1
    assert t_kpis.json()["in_progress"] == 1

    await client.post(
        "/api/v1/quality/samples",
        headers=auth,
        json={
            "lot_id": lot["id"],
            "method": "gravimetry",
            "measured_purity": "0.74",
            "result": "approved",
        },
    )
    q_kpis = await client.get("/api/v1/quality/kpis", headers=auth)
    assert q_kpis.json()["total_samples"] == 1
    assert q_kpis.json()["approved"] == 1


async def test_lab_role_can_sample_but_not_transform(client: AsyncClient) -> None:
    tenant = await _provision(client)
    admin_auth = await _admin_auth(client, tenant)
    materials = await _materials(client, admin_auth)
    au18 = next(m for m in materials if m["code"] == "AU18")
    lot = await _make_lot(client, admin_auth, au18["id"])

    email = _unique("lab") + "@example.com"
    await client.post(
        "/api/v1/users",
        headers=admin_auth,
        json={
            "email": email,
            "full_name": "Analista",
            "password": "Analista-123",
            "role_slug": "laboratorio",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": email, "password": "Analista-123"},
    )
    lab_auth = _bearer(login.json()["access_token"])

    # laboratorio tiene quality:manage → puede registrar muestra.
    sample = await client.post(
        "/api/v1/quality/samples",
        headers=lab_auth,
        json={
            "lot_id": lot["id"],
            "method": "xrf",
            "measured_purity": "0.75",
            "result": "approved",
        },
    )
    assert sample.status_code == 201, sample.text

    # Pero no tiene transformation:access → 403 al listar OT.
    forbidden = await client.get("/api/v1/transformation/orders", headers=lab_auth)
    assert forbidden.status_code == 403
