"""Pruebas E2E de Fase 6: Contabilidad y Tesorería (criterios de aceptación).

Verifican que: (1) aprobar una compra y registrar una venta generan asientos de
doble partida balanceados (Σdébitos = Σcréditos); (2) el Balance General siempre
cuadra (Activos = Pasivos + Patrimonio); (3) la cartera (CxC/CxP) se deriva por
tercero del libro mayor; (4) un pago reduce la cartera; (5) un asiento manual
desbalanceado se rechaza. Contra PostgreSQL real con el rol de aplicación (RLS).
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
    return resp.json()[0]


async def _supplier(client: AsyncClient, auth: dict) -> dict:
    resp = await client.post(
        "/api/v1/suppliers",
        headers=auth,
        json={"legal_name": "Minera del Chocó", "tax_id": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _customer(client: AsyncClient, auth: dict) -> dict:
    resp = await client.post(
        "/api/v1/customers",
        headers=auth,
        json={"legal_name": "Global Metals Corp.", "tax_id": _unique("NIT")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _lot(client: AsyncClient, auth: dict, material: dict, **over: object) -> dict:
    body = {
        "material_id": material["id"],
        "form": "refined",
        "declared_purity": "0.999",
        "gross_weight_g": "500",
        "price_per_oz": "3000",
        **over,
    }
    resp = await client.post("/api/v1/inventory/lots", headers=auth, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _assert_all_entries_balanced(entries: list[dict]) -> None:
    for entry in entries:
        assert float(entry["total_debit"]) == float(entry["total_credit"]), entry


async def test_provisioning_seeds_chart_of_accounts(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    resp = await client.get("/api/v1/accounting/accounts", headers=auth)
    assert resp.status_code == 200, resp.text
    codes = {a["code"] for a in resp.json()}
    assert {"1105", "1305", "1435", "2205", "4135", "6135"} <= codes


async def test_purchase_approval_posts_balanced_entry(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    supplier = await _supplier(client, auth)

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
    order = created.json()
    # Antes de aprobar no hay asientos.
    assert (await client.get("/api/v1/accounting/journal", headers=auth)).json() == []

    approved = await client.post(f"/api/v1/purchasing/orders/{order['id']}/approve", headers=auth)
    assert approved.status_code == 200, approved.text

    journal = (await client.get("/api/v1/accounting/journal", headers=auth)).json()
    assert len(journal) == 1
    entry = journal[0]
    assert entry["source_type"] == "purchase"
    assert float(entry["total_debit"]) == float(entry["total_credit"]) > 0
    accounts = {line["account_code"] for line in entry["lines"]}
    assert {"1435", "2205"} <= accounts  # Dr Inventario / Cr CxP

    # La cuenta por pagar del proveedor aparece en el submayor.
    payables = (await client.get("/api/v1/accounting/payables", headers=auth)).json()
    assert any(p["party_id"] == supplier["id"] for p in payables)
    payable = next(p for p in payables if p["party_id"] == supplier["id"])
    assert float(payable["balance"]) == pytest.approx(float(entry["total_debit"]))


async def test_sale_posts_receivable_and_balance_sheet_balances(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    customer = await _customer(client, auth)
    lot = await _lot(client, auth, material, gross_weight_g="500", price_per_oz="3000")

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

    journal = (await client.get("/api/v1/accounting/journal", headers=auth)).json()
    sale_entry = next(e for e in journal if e["source_type"] == "sale")
    accounts = {line["account_code"] for line in sale_entry["lines"]}
    assert {"1305", "4135", "6135", "1435"} <= accounts  # CxC/Ingresos/Costo/Inventario
    _assert_all_entries_balanced(journal)

    receivables = (await client.get("/api/v1/accounting/receivables", headers=auth)).json()
    assert any(r["party_id"] == customer["id"] for r in receivables)

    # Criterio de aceptación: el Balance General cuadra.
    balance = (await client.get("/api/v1/accounting/balance-sheet", headers=auth)).json()
    assert balance["is_balanced"] is True
    assert float(balance["total_assets"]) == pytest.approx(
        float(balance["total_liabilities"]) + float(balance["total_equity"])
    )
    # Hubo utilidad (precio de venta > costo del lote).
    assert float(balance["result_for_period"]) > 0


async def test_payment_reduces_receivable(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    customer = await _customer(client, auth)
    lot = await _lot(client, auth, material, gross_weight_g="500", price_per_oz="3000")

    await client.post(
        "/api/v1/sales/orders",
        headers=auth,
        json={
            "customer_id": customer["id"],
            "lot_id": lot["id"],
            "quantity_g": "200",
            "price_per_oz": "3200",
        },
    )
    before = (await client.get("/api/v1/accounting/receivables", headers=auth)).json()
    owed = float(next(r for r in before if r["party_id"] == customer["id"])["balance"])

    pay = await client.post(
        "/api/v1/accounting/payments",
        headers=auth,
        json={
            "direction": "inbound",
            "party_id": customer["id"],
            "party_name": customer["legal_name"],
            "amount": f"{owed / 2:.2f}",
        },
    )
    assert pay.status_code == 201, pay.text

    after = (await client.get("/api/v1/accounting/receivables", headers=auth)).json()
    remaining = float(next(r for r in after if r["party_id"] == customer["id"])["balance"])
    assert remaining == pytest.approx(owed / 2, abs=0.02)


async def test_sale_cancellation_reverses_entry(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)
    customer = await _customer(client, auth)
    lot = await _lot(client, auth, material, gross_weight_g="500", price_per_oz="3000")

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
    await client.patch(
        f"/api/v1/sales/orders/{sale.json()['id']}/status",
        headers=auth,
        json={"status": "cancelled"},
    )

    journal = (await client.get("/api/v1/accounting/journal", headers=auth)).json()
    assert any(e["source_type"] == "sale_reversal" for e in journal)
    _assert_all_entries_balanced(journal)
    # Tras la reversa, la CxC del cliente queda saldada.
    receivables = (await client.get("/api/v1/accounting/receivables", headers=auth)).json()
    assert all(r["party_id"] != customer["id"] for r in receivables)


async def test_manual_unbalanced_entry_rejected(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    bad = await client.post(
        "/api/v1/accounting/journal",
        headers=auth,
        json={
            "memo": "Ajuste mal cuadrado",
            "lines": [
                {"account_code": "1105", "debit": "100.00"},
                {"account_code": "4135", "credit": "90.00"},
            ],
        },
    )
    assert bad.status_code == 422, bad.text
    assert bad.json()["error"] == "unbalanced_entry"

    good = await client.post(
        "/api/v1/accounting/journal",
        headers=auth,
        json={
            "memo": "Aporte de capital inicial",
            "lines": [
                {"account_code": "1110", "debit": "100.00"},
                {"account_code": "3115", "credit": "100.00"},
            ],
        },
    )
    assert good.status_code == 201, good.text
    assert float(good.json()["total_debit"]) == 100.0


async def test_accounting_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)
    auth_a = await _admin_auth(client, tenant_a)
    auth_b = await _admin_auth(client, tenant_b)

    await client.post(
        "/api/v1/accounting/journal",
        headers=auth_a,
        json={
            "memo": "Capital A",
            "lines": [
                {"account_code": "1110", "debit": "500.00"},
                {"account_code": "3115", "credit": "500.00"},
            ],
        },
    )
    # El tenant B no ve los asientos de A (RLS).
    journal_b = (await client.get("/api/v1/accounting/journal", headers=auth_b)).json()
    assert journal_b == []
