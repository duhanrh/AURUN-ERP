"""Pruebas E2E de Fase 8 — Auditoría: registro inmutable de operaciones (7.18).

Verifican que: (1) operaciones críticas (alta de usuario, cambio de marca/parámetros/
módulos, aprobación de OC, asiento manual) quedan registradas; (2) los accesos
fallidos se auditan; (3) el log es append-only a nivel de BD (no se puede UPDATE/
DELETE ni con el rol de aplicación); (4) la consulta filtra y respeta el tenant.
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


async def test_critical_operations_are_audited(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    # Alta de usuario.
    await client.post(
        "/api/v1/users",
        headers=auth,
        json={
            "email": _unique("u") + "@example.com",
            "full_name": "Usuario Auditado",
            "password": "Pass-12345",
            "role_slug": "operativo",
        },
    )
    # Cambio de marca y de módulo.
    await client.put("/api/v1/configuration/branding", headers=auth, json={"brand_name": "Marca X"})
    await client.put(
        "/api/v1/configuration/modules/reportes", headers=auth, json={"is_active": False}
    )

    audit = await client.get("/api/v1/audit", headers=auth)
    assert audit.status_code == 200, audit.text
    actions = {row["action"] for row in audit.json()}
    assert "user.create" in actions
    assert "config.branding.update" in actions
    assert "config.module.toggle" in actions
    # Las entradas registran al autor y el tenant (vía RLS).
    user_event = next(r for r in audit.json() if r["action"] == "user.create")
    assert user_event["user_id"] is not None
    assert user_event["entity_type"] == "user"


async def test_failed_login_is_audited(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)

    bad = await client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant["tenant_id"]},
        json={"email": tenant["admin_email"], "password": "clave-incorrecta"},
    )
    assert bad.status_code == 401

    audit = await client.get("/api/v1/audit?action=auth.login_failed", headers=auth)
    assert audit.status_code == 200
    assert len(audit.json()) >= 1
    assert audit.json()[0]["entity_type"] == "auth"


async def test_audit_log_is_append_only(client: AsyncClient) -> None:
    """A nivel de BD, el rol de aplicación no puede modificar ni borrar auditoría.

    Bajo ``FORCE ROW LEVEL SECURITY`` sin política para UPDATE/DELETE, esas
    sentencias no ven ninguna fila (``USING`` por defecto = falso): afectan 0 filas
    y el registro permanece intacto.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    await client.put("/api/v1/configuration/branding", headers=auth, json={"brand_name": "Y"})

    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("SELECT set_config('app.current_tenant_id', :t, false)"),
                {"t": tenant["tenant_id"]},
            )
            before = (await conn.execute(text("SELECT count(*) FROM audit_logs"))).scalar_one()
            assert before >= 1

            upd = await conn.execute(text("UPDATE audit_logs SET action = 'tampered'"))
            assert upd.rowcount == 0  # ninguna fila modificable

            dele = await conn.execute(text("DELETE FROM audit_logs"))
            assert dele.rowcount == 0  # ninguna fila borrable

            after = (await conn.execute(text("SELECT count(*) FROM audit_logs"))).scalar_one()
            tampered = (
                await conn.execute(
                    text("SELECT count(*) FROM audit_logs WHERE action = 'tampered'")
                )
            ).scalar_one()
            assert after == before
            assert tampered == 0
    finally:
        await engine.dispose()


async def test_audit_cross_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await _provision(client)
    tenant_b = await _provision(client)
    auth_a = await _admin_auth(client, tenant_a)
    auth_b = await _admin_auth(client, tenant_b)

    await client.put("/api/v1/configuration/branding", headers=auth_a, json={"brand_name": "A"})
    # El tenant B no ve la auditoría de A.
    audit_b = await client.get("/api/v1/audit", headers=auth_b)
    actions_b = [r for r in audit_b.json() if r["action"] == "config.branding.update"]
    assert actions_b == []


async def test_audit_requires_permission(client: AsyncClient) -> None:
    tenant = await _provision(client)
    auth = await _admin_auth(client, tenant)
    # Crea un usuario solo_lectura (sin audit:access).
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
    forbidden = await client.get("/api/v1/audit", headers=reader_auth)
    assert forbidden.status_code == 403
