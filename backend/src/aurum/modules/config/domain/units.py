"""Dominio de Unidades de Medida configurables (sección 7.17 / plantillas de impresión).

El negocio de metales preciosos usa unidades tradicionales además del gramo
(castellano, tomín, grano…) y el usuario final quiere ver los pesos y precios en
la unidad que mejor entiende. Modelamos cada unidad por su **factor a gramos**
(``grams_factor`` = gramos que equivalen a 1 unidad), lo que permite convertir
cualquier peso entre unidades pasando por el gramo como base.

Los valores sembrados son los tradicionales colombianos para oro/platino, pero son
**editables por tenant** (de ahí que vivan en una tabla configurable, no como
constantes): ``1 castellano = 8 tomines = 96 granos ≈ 4.6 g``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class UnitDef:
    code: str
    name: str
    symbol: str
    grams_factor: Decimal
    is_base: bool = False


# Catálogo base sembrado en cada tenant. El gramo es la unidad base (factor 1).
BASE_UNITS: tuple[UnitDef, ...] = (
    UnitDef("gramo", "Gramo", "g", Decimal("1"), is_base=True),
    UnitDef("grano", "Grano", "gr", Decimal("0.04791667")),
    UnitDef("tomin", "Tomín", "to", Decimal("0.575")),
    UnitDef("castellano", "Castellano", "ct", Decimal("4.6")),
    UnitDef("onza_troy", "Onza troy", "ozt", Decimal("31.1034768")),
    UnitDef("libra", "Libra", "lb", Decimal("453.59237")),
    UnitDef("kilogramo", "Kilogramo", "kg", Decimal("1000")),
)

BASE_UNIT_CODE = "gramo"


def grams_to_unit(grams: Decimal, grams_factor: Decimal) -> Decimal:
    """Convierte un peso en gramos a la unidad cuyo factor es ``grams_factor``."""
    if grams_factor <= 0:
        raise ValueError("El factor a gramos debe ser mayor que cero.")
    return grams / grams_factor


def unit_to_grams(quantity: Decimal, grams_factor: Decimal) -> Decimal:
    """Convierte una cantidad expresada en una unidad a su peso en gramos."""
    return quantity * grams_factor
