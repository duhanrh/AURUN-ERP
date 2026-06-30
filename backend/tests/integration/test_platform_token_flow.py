"""Pruebas del guard de la API de plataforma (``X-Platform-Admin-Token``).

Cubren el límite de seguridad del provisionamiento de tenants (sección 5.7), que
no tenía cobertura directa:

1. Fuera de ``local`` sin token configurado → 403 (no se permite bootstrap abierto).
2. Token configurado pero cabecera ausente o inválida → 403.
3. Token configurado y cabecera correcta → 201 (provisiona).
4. En ``local`` sin token → 201 (bootstrap abierto, comportamiento documentado).
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


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _payload() -> dict[str, str]:
    sub = _unique("acme")
    return {
        "name": "ACME Metales",
        "subdomain": sub,
        "admin_email": f"admin-{sub}@example.com",
        "admin_full_name": "Admin Minero",
        "admin_password": "Admin-12345",
    }


async def _client_with(*, env: str, token: str) -> AsyncIterator[AsyncClient]:
    """Cliente cuya configuración fuerza ``env`` y ``platform_admin_token``.

    Se parte de la configuración real (para conservar la conexión a la BD) y se
    sobreescriben solo los dos campos relevantes vía ``dependency_overrides``.
    """
    app = create_app()
    base = get_settings()
    overridden = base.model_copy(update={"env": env, "platform_admin_token": token})
    app.dependency_overrides[get_settings] = lambda: overridden
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_non_local_without_token_is_forbidden() -> None:
    async for client in _client_with(env="development", token=""):
        resp = await client.post("/api/v1/platform/tenants", json=_payload())
        assert resp.status_code == 403, resp.text
        assert resp.json()["error"] == "authorization_error"


async def test_configured_token_requires_matching_header() -> None:
    async for client in _client_with(env="development", token="s3cret-token"):
        # Sin cabecera → 403.
        missing = await client.post("/api/v1/platform/tenants", json=_payload())
        assert missing.status_code == 403, missing.text
        # Cabecera incorrecta → 403.
        wrong = await client.post(
            "/api/v1/platform/tenants",
            json=_payload(),
            headers={"X-Platform-Admin-Token": "nope"},
        )
        assert wrong.status_code == 403, wrong.text


async def test_configured_token_with_correct_header_provisions() -> None:
    async for client in _client_with(env="development", token="s3cret-token"):
        resp = await client.post(
            "/api/v1/platform/tenants",
            json=_payload(),
            headers={"X-Platform-Admin-Token": "s3cret-token"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["roles_created"] >= 1


async def test_local_without_token_is_open() -> None:
    async for client in _client_with(env="local", token=""):
        resp = await client.post("/api/v1/platform/tenants", json=_payload())
        assert resp.status_code == 201, resp.text
