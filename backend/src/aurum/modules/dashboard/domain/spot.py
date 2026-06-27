"""Adaptador de precios spot de metales preciosos (sección 7.16).

En producción, un adaptador de infraestructura consulta un proveedor externo
(XAU/XAG/XPT/XPD) con caché de corta duración. Aquí se entrega un **fallback
estático** marcado como ``stale=True``: el sistema degrada de forma controlada
(muestra el último precio conocido) en lugar de romper el Dashboard cuando no hay
proveedor configurado. La forma del dato es la definitiva; solo cambia la fuente.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SpotPrice:
    symbol: str  # XAU / XAG / XPT / XPD
    name: str
    price_usd_per_oz: Decimal
    change_pct: Decimal
    stale: bool


# Último precio conocido por símbolo (USD/oz troy) — fallback de degradación.
_FALLBACK: tuple[tuple[str, str, str, str], ...] = (
    ("XAU", "Oro", "2412.50", "0.8"),
    ("XAG", "Plata", "31.20", "-0.4"),
    ("XPT", "Platino", "1015.00", "1.2"),
    ("XPD", "Paladio", "945.00", "-1.1"),
)


def get_spot_prices() -> list[SpotPrice]:
    """Devuelve los precios spot (fallback estático marcado como no actualizado)."""
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
