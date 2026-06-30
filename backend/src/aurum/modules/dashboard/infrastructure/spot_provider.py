"""Adaptador de precios spot en vivo con caché de corta duración y degradación.

Reglas (sección 7.16):
- Si la respuesta cacheada sigue fresca (< TTL), se devuelve sin llamar a la red.
- Si el proveedor no está configurado (``spot_provider_url`` vacío), se degrada al
  fallback estático (``stale=true``) sin tocar la red — así dev/tests son deterministas.
- Si la llamada falla (timeout/HTTP/parse), se degrada al **último precio conocido**
  (marcado ``stale``) o, si no hay, al fallback estático. Nunca rompe el Dashboard.

Contrato del proveedor (configurable): JSON con ``prices`` = USD/oz por símbolo, o
``rates`` = metal-por-USD por símbolo (se invierte a USD/oz). Un proxy del despliegue
puede adaptar cualquier vendor a este contrato.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal, InvalidOperation

from aurum.modules.dashboard.domain.spot import (
    SPOT_NAMES,
    SPOT_SYMBOLS,
    SpotPrice,
    static_fallback,
)
from aurum.shared.config import Settings, get_settings

logger = logging.getLogger("aurum.spot")

# Caché en proceso: (epoch_monotónico, precios). Suficiente para una sola instancia;
# en multi-instancia se respaldaría en Redis (sección 10.9), misma forma de decisión.
_cache: tuple[float, list[SpotPrice]] | None = None


def reset_cache() -> None:
    """Limpia la caché (uso en pruebas)."""
    global _cache
    _cache = None


async def _http_fetch(settings: Settings) -> dict[str, object]:
    """Hace la petición HTTP al proveedor configurado. Aislado para poder simularlo."""
    import httpx

    headers = {"Accept": "application/json"}
    params: dict[str, str] = {}
    if settings.spot_api_key:
        headers["X-API-KEY"] = settings.spot_api_key
        params["api_key"] = settings.spot_api_key
    async with httpx.AsyncClient(timeout=settings.spot_request_timeout_seconds) as cli:
        resp = await cli.get(settings.spot_provider_url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    return data if isinstance(data, dict) else {}


def _to_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse(payload: dict[str, object]) -> list[SpotPrice]:
    """Convierte la respuesta del proveedor a precios USD/oz por símbolo."""
    prices_raw = payload.get("prices")
    rates_raw = payload.get("rates")
    by_symbol: dict[str, Decimal] = {}

    if isinstance(prices_raw, dict):
        for sym in SPOT_SYMBOLS:
            d = _to_decimal(prices_raw.get(sym))
            if d is not None and d > 0:
                by_symbol[sym] = d
    elif isinstance(rates_raw, dict):
        for sym in SPOT_SYMBOLS:
            rate = _to_decimal(rates_raw.get(sym))
            if rate is not None and rate > 0:
                by_symbol[sym] = (Decimal(1) / rate).quantize(Decimal("0.01"))

    if not by_symbol:
        raise ValueError("Respuesta de precios spot sin símbolos reconocibles.")

    # Cambios opcionales del proveedor (``changes`` por símbolo); si no, 0.
    changes_raw = payload.get("changes")
    changes = changes_raw if isinstance(changes_raw, dict) else {}

    result: list[SpotPrice] = []
    for sym in SPOT_SYMBOLS:
        if sym not in by_symbol:
            continue
        change = _to_decimal(changes.get(sym)) or Decimal("0")
        result.append(
            SpotPrice(
                symbol=sym,
                name=SPOT_NAMES[sym],
                price_usd_per_oz=by_symbol[sym],
                change_pct=change,
                stale=False,
            )
        )
    return result


def _degraded() -> list[SpotPrice]:
    """Último precio conocido (marcado stale) o el fallback estático."""
    if _cache is not None:
        return [
            SpotPrice(p.symbol, p.name, p.price_usd_per_oz, p.change_pct, stale=True)
            for p in _cache[1]
        ]
    return static_fallback()


async def get_spot_prices(settings: Settings | None = None) -> list[SpotPrice]:
    """Precios spot en vivo con caché; degrada de forma controlada si no hay/falla."""
    global _cache
    settings = settings or get_settings()

    # Sin proveedor configurado: fallback estático directo (no se sirve un precio
    # cacheado de cuando sí lo hubo como si fuese vigente).
    if not settings.spot_provider_url:
        return static_fallback()

    now = time.monotonic()
    if _cache is not None and now - _cache[0] < settings.spot_cache_ttl_seconds:
        return _cache[1]

    try:
        payload = await _http_fetch(settings)
        prices = _parse(payload)
    except Exception as exc:  # noqa: BLE001 — degradación controlada, nunca romper
        logger.warning("Precios spot no disponibles (%s); se degrada al último conocido.", exc)
        return _degraded()

    _cache = (now, prices)
    return prices
