"""Fixtures de las pruebas de integración.

El engine de SQLAlchemy es un singleton perezoso ligado al event loop donde se
crea. pytest-asyncio usa un loop por prueba, así que reiniciamos el singleton
antes de cada prueba (engine fresco en el loop actual) y lo liberamos en el
teardown, dentro del mismo loop, evitando errores de "event loop is closed".
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

import aurum.shared.infrastructure.database as db


@pytest.fixture(autouse=True)
async def _fresh_engine() -> AsyncIterator[None]:
    db._engine = None
    db._session_factory = None
    try:
        yield
    finally:
        await db.dispose_engine()
