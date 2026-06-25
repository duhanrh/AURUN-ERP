"""Fixtures compartidas de la suite de pruebas."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aurum.main import create_app


@pytest.fixture
async def client() -> AsyncClient:
    """Cliente HTTP async apuntando a la app FastAPI en memoria (sin red real)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
