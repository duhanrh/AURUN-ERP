"""Pruebas de aislamiento multi-tenant vía Row Level Security (secciones 5.5/9.3).

Verifican, contra una PostgreSQL real y conectando con el rol de aplicación
(NOBYPASSRLS), que un tenant nunca ve ni puede escribir datos de otro tenant.
Se omiten automáticamente si la base de datos no está disponible.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from aurum.shared.config import get_settings


@pytest.fixture
async def conn() -> AsyncIterator[AsyncConnection]:
    """Conexión a la BD de pruebas; omite la prueba si no hay BD accesible."""
    engine = create_async_engine(get_settings().database_url)
    try:
        connection = await engine.connect()
    except Exception:  # noqa: BLE001 — cualquier fallo de conexión => skip
        await engine.dispose()
        pytest.skip("PostgreSQL no disponible para pruebas de integración")

    try:
        yield connection
    finally:
        await connection.close()
        await engine.dispose()


async def _insert_tenant(conn: AsyncConnection, tenant_id: uuid.UUID) -> None:
    await conn.execute(
        text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, :name, :sub)"),
        {"id": tenant_id, "name": "Test Tenant", "sub": f"t-{tenant_id.hex[:12]}"},
    )


async def _set_tenant(conn: AsyncConnection, tenant_id: uuid.UUID | None) -> None:
    value = "" if tenant_id is None else str(tenant_id)
    await conn.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": value},
    )


async def _insert_branding(conn: AsyncConnection, tenant_id: uuid.UUID, name: str) -> None:
    await conn.execute(
        text(
            "INSERT INTO tenant_branding (tenant_id, brand_name, is_customized) "
            "VALUES (:tid, :name, true)"
        ),
        {"tid": tenant_id, "name": name},
    )


async def test_branding_visible_only_for_own_tenant(conn: AsyncConnection) -> None:
    trans = await conn.begin()
    try:
        a, b = uuid.uuid4(), uuid.uuid4()
        await _insert_tenant(conn, a)
        await _insert_tenant(conn, b)

        await _set_tenant(conn, a)
        await _insert_branding(conn, a, "Marca A")
        await _set_tenant(conn, b)
        await _insert_branding(conn, b, "Marca B")

        # Contexto del Tenant A: solo debe ver su propia marca.
        await _set_tenant(conn, a)
        visible = (
            (await conn.execute(text("SELECT tenant_id FROM tenant_branding"))).scalars().all()
        )
        assert visible == [a]

        # Contexto del Tenant B: solo debe ver la suya.
        await _set_tenant(conn, b)
        visible_b = (
            (await conn.execute(text("SELECT tenant_id FROM tenant_branding"))).scalars().all()
        )
        assert visible_b == [b]
    finally:
        await trans.rollback()


async def test_branding_hidden_without_tenant_context(conn: AsyncConnection) -> None:
    trans = await conn.begin()
    try:
        a = uuid.uuid4()
        await _insert_tenant(conn, a)
        await _set_tenant(conn, a)
        await _insert_branding(conn, a, "Marca A")

        # Sin tenant fijado, la política niega por defecto (NULL): 0 filas.
        await _set_tenant(conn, None)
        count = (await conn.execute(text("SELECT count(*) FROM tenant_branding"))).scalar()
        assert count == 0
    finally:
        await trans.rollback()


async def test_with_check_blocks_cross_tenant_insert(conn: AsyncConnection) -> None:
    trans = await conn.begin()
    try:
        a, b = uuid.uuid4(), uuid.uuid4()
        await _insert_tenant(conn, a)
        await _insert_tenant(conn, b)

        # Contexto A intentando escribir una marca del Tenant B => WITH CHECK lo bloquea.
        await _set_tenant(conn, a)
        with pytest.raises(DBAPIError):
            await _insert_branding(conn, b, "Marca B falsificada")
    finally:
        await trans.rollback()
