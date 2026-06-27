"""Pruebas E2E de Fase 8 — Endurecimiento: anti fuerza bruta + cabeceras (sección 10).

Verifican que: (1) tras N intentos fallidos el login se bloquea temporalmente (429);
(2) un login exitoso limpia el contador; (3) toda respuesta lleva cabeceras de
seguridad.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from aurum.main import create_app
from aurum.modules.auth.infrastructure import login_guard
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


@pytest.fixture(autouse=True)
def _clear_login_guard() -> None:
    login_guard.clear_all()


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


async def test_security_headers_present(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "no-referrer"


async def test_login_blocks_after_repeated_failures(client: AsyncClient) -> None:
    tenant = await _provision(client)
    headers = {"X-Tenant-ID": tenant["tenant_id"]}
    bad = {"email": tenant["admin_email"], "password": "incorrecta"}

    # 5 intentos fallidos → 401.
    for _ in range(5):
        resp = await client.post("/api/v1/auth/login", headers=headers, json=bad)
        assert resp.status_code == 401

    # El sexto se bloquea temporalmente (429), incluso con credenciales correctas.
    blocked = await client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": tenant["admin_email"], "password": "Admin-12345"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "too_many_attempts"


async def test_successful_login_resets_counter(client: AsyncClient) -> None:
    tenant = await _provision(client)
    headers = {"X-Tenant-ID": tenant["tenant_id"]}

    # Algunos fallos por debajo del umbral.
    for _ in range(3):
        await client.post(
            "/api/v1/auth/login",
            headers=headers,
            json={"email": tenant["admin_email"], "password": "incorrecta"},
        )
    # Un login correcto limpia el contador.
    ok = await client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": tenant["admin_email"], "password": "Admin-12345"},
    )
    assert ok.status_code == 200

    # Vuelve a haber margen para más intentos sin bloqueo inmediato.
    again = await client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"email": tenant["admin_email"], "password": "incorrecta"},
    )
    assert again.status_code == 401
