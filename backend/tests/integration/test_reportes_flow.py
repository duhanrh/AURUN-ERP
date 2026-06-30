"""Pruebas E2E de Fase 7 — Reportes: datos reales y exportación (sección 7.15).

Verifican que: (1) el catálogo expone los 6 reportes; (2) cada reporte se genera
con datos reales del tenant y cabecera de marca; (3) la exportación entrega un CSV
real descargable; (4) la marca personalizada aparece en la cabecera del reporte;
(5) un reporte inexistente da 404.
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
    return (await client.get("/api/v1/inventory/materials", headers=auth)).json()[0]


async def test_report_catalog_lists_six(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    resp = await client.get("/api/v1/reports", headers=auth)
    assert resp.status_code == 200, resp.text
    keys = {r["key"] for r in resp.json()}
    assert {
        "inventory_valued",
        "profit_loss",
        "lot_traceability",
        "regulatory",
        "operational_kpis",
        "price_analysis",
    } == keys


async def test_inventory_valued_uses_real_data(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    material = await _first_material(client, auth)

    await client.post(
        "/api/v1/inventory/lots",
        headers=auth,
        json={
            "material_id": material["id"],
            "form": "refined",
            "declared_purity": "0.999",
            "gross_weight_g": "500",
            "price_per_oz": "3000",
        },
    )

    report = await client.get("/api/v1/reports/inventory_valued", headers=auth)
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["title"] == "Inventario Valorizado"
    assert body["brand_name"] == "AURUM ERP"  # sin personalizar → marca por defecto
    assert body["document_number"].startswith("REP-")
    assert len(body["rows"]) == 1
    assert body["rows"][0][0].startswith("LOT-")
    # Resumen con valor total > 0.
    total = next(s for s in body["summary"] if s["label"] == "Valor total")
    assert total["value"].startswith("$")


async def test_report_export_returns_csv(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    resp = await client.get("/api/v1/reports/operational_kpis/export", headers=auth)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    text = resp.text
    assert "AURUM ERP" in text
    assert "KPIs Operativos" in text
    assert "Lotes en inventario" in text


async def test_report_export_xlsx_and_pdf(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    # Excel real: cabecera ZIP "PK" y content-type de xlsx; nombre con .xlsx.
    xlsx = await client.get("/api/v1/reports/operational_kpis/export?format=xlsx", headers=auth)
    assert xlsx.status_code == 200, xlsx.text
    assert "spreadsheetml" in xlsx.headers["content-type"]
    assert xlsx.headers["content-disposition"].endswith('.xlsx"')
    assert xlsx.content[:2] == b"PK"

    # PDF real: cabecera "%PDF" y content-type application/pdf.
    pdf = await client.get("/api/v1/reports/operational_kpis/export?format=pdf", headers=auth)
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.headers["content-disposition"].endswith('.pdf"')
    assert pdf.content[:4] == b"%PDF"

    # El análisis de precios usa "Δ%": el PDF no debe romper (se transliteró).
    pdf2 = await client.get("/api/v1/reports/price_analysis/export?format=pdf", headers=auth)
    assert pdf2.status_code == 200
    assert pdf2.content[:4] == b"%PDF"


async def test_report_header_uses_custom_brand(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    await client.put(
        "/api/v1/configuration/branding",
        headers=auth,
        json={"brand_name": "Oro Andino S.A."},
    )
    report = await client.get("/api/v1/reports/profit_loss", headers=auth)
    assert report.json()["brand_name"] == "Oro Andino S.A."


async def test_unknown_report_404(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    resp = await client.get("/api/v1/reports/inexistente", headers=auth)
    assert resp.status_code == 404
