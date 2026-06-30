"""Pruebas del adaptador de precios spot: parseo, caché y degradación (sección 7.16).

No tocan la red: se simula ``_http_fetch``. Validan que sin proveedor configurado se
degrada al fallback estático (``stale``), que parsea ``prices`` (USD/oz) y ``rates``
(metal-por-USD, se invierte), que cachea, y que ante fallo degrada al último conocido.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from aurum.modules.dashboard.infrastructure import spot_provider as sp
from aurum.shared.config import Settings


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    sp.reset_cache()


def _settings(**over: Any) -> Settings:
    base = {
        "spot_provider_url": "https://spot.example/quote",
        "spot_api_key": "",
        "spot_cache_ttl_seconds": 300,
        "spot_request_timeout_seconds": 1.0,
    }
    base.update(over)
    return Settings(**base)  # type: ignore[arg-type]


async def test_unconfigured_degrades_to_static() -> None:
    prices = await sp.get_spot_prices(_settings(spot_provider_url=""))
    assert {p.symbol for p in prices} == {"XAU", "XAG", "XPT", "XPD"}
    assert all(p.stale for p in prices)


async def test_parses_direct_prices(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch(_: Settings) -> dict[str, object]:
        return {"prices": {"XAU": "2500", "XAG": "33.5", "XPT": "1000", "XPD": "950"}}

    monkeypatch.setattr(sp, "_http_fetch", fake_fetch)
    prices = await sp.get_spot_prices(_settings())
    by = {p.symbol: p for p in prices}
    assert by["XAU"].price_usd_per_oz == Decimal("2500")
    assert all(not p.stale for p in prices)


async def test_parses_rates_inverted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch(_: Settings) -> dict[str, object]:
        return {"rates": {"XAU": "0.0004", "XAG": "0.03"}}  # metal por USD

    monkeypatch.setattr(sp, "_http_fetch", fake_fetch)
    prices = await sp.get_spot_prices(_settings())
    by = {p.symbol: p for p in prices}
    assert by["XAU"].price_usd_per_oz == Decimal("2500.00")  # 1 / 0.0004
    assert by["XAG"].stale is False


async def test_cache_avoids_second_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    async def fake_fetch(_: Settings) -> dict[str, object]:
        calls["n"] += 1
        return {"prices": {"XAU": "2400"}}

    monkeypatch.setattr(sp, "_http_fetch", fake_fetch)
    settings = _settings()
    await sp.get_spot_prices(settings)
    await sp.get_spot_prices(settings)  # dentro del TTL → no vuelve a llamar
    assert calls["n"] == 1


async def test_failure_degrades_to_last_known(monkeypatch: pytest.MonkeyPatch) -> None:
    state = {"fail": False}

    async def fake_fetch(_: Settings) -> dict[str, object]:
        if state["fail"]:
            raise RuntimeError("proveedor caído")
        return {"prices": {"XAU": "2600", "XAG": "30"}}

    monkeypatch.setattr(sp, "_http_fetch", fake_fetch)
    settings = _settings(spot_cache_ttl_seconds=0)  # fuerza re-fetch cada vez

    fresh = await sp.get_spot_prices(settings)
    assert all(not p.stale for p in fresh)

    state["fail"] = True
    degraded = await sp.get_spot_prices(settings)
    by = {p.symbol: p for p in degraded}
    assert by["XAU"].price_usd_per_oz == Decimal("2600")  # último conocido
    assert all(p.stale for p in degraded)  # pero marcado como no actualizado
