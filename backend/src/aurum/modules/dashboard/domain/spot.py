"""Dominio de precios spot de metales preciosos (XAU/XAG/XPT/XPD), sección 7.16.

Aquí viven el value object ``SpotPrice``, los nombres por símbolo y el **fallback
estático** (último precio conocido marcado ``stale=True``). La obtención en vivo y la
caché viven en infraestructura (``infrastructure/spot_provider.py``): si el proveedor
no está configurado o falla, el sistema degrada de forma controlada a este fallback en
lugar de romper el Dashboard.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SpotPrice:
    symbol: str  # XAU / XAG / XPT / XPD
    name: str
    price_usd_per_oz: Decimal
    change_pct: Decimal
    stale: bool


# Nombre y último precio conocido por símbolo (USD/oz troy) — fallback de degradación.
_FALLBACK: tuple[tuple[str, str, str, str], ...] = (
    ("XAU", "Oro", "2412.50", "0.8"),
    ("XAG", "Plata", "31.20", "-0.4"),
    ("XPT", "Platino", "1015.00", "1.2"),
    ("XPD", "Paladio", "945.00", "-1.1"),
)

SPOT_SYMBOLS: tuple[str, ...] = tuple(s for s, *_ in _FALLBACK)
SPOT_NAMES: dict[str, str] = {s: name for s, name, *_ in _FALLBACK}


# Abstracción que la capa de aplicación recibe inyectada (la impl. en vivo vive en
# infraestructura): obtener los precios spot actuales de forma asíncrona.
SpotProvider = Callable[[], Awaitable[list["SpotPrice"]]]


def static_fallback() -> list[SpotPrice]:
    """Último precio conocido por símbolo, marcado como no actualizado (``stale``)."""
    return [
        SpotPrice(
            symbol=symbol,
            name=name,
            price_usd_per_oz=Decimal(price),
            change_pct=Decimal(change),
            stale=True,
        )
        for symbol, name, price, change in _FALLBACK
    ]
