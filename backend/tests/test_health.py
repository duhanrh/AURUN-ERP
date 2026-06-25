"""Prueba de humo: la app arranca y el endpoint de salud responde."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aurum-erp-backend"
    assert "version" in body
