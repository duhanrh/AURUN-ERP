"""Reglas de dominio del Inventario: vocabulario y valorización (sección 7.1).

Valorización = ``peso fino × precio``, donde el peso fino son las onzas troy de
metal puro contenidas: ``gramos_brutos × pureza ÷ gramos_por_onza_troy``. Toda la
aritmética usa ``Decimal`` para no arrastrar error de coma flotante en dinero/peso.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, get_args

# Gramos en una onza troy (unidad estándar de cotización de metales preciosos).
TROY_OUNCE_G = Decimal("31.1034768")

LotForm = Literal["raw", "refined"]
"""Forma del material: crudo (raw) o refinado (refined)."""

LotStatus = Literal["available", "reserved", "in_process", "low_stock", "quarantine"]
"""Estado del lote (réplica de los badges de inventario de la maqueta)."""

LOT_FORMS: tuple[LotForm, ...] = get_args(LotForm)
LOT_STATUSES: tuple[LotStatus, ...] = get_args(LotStatus)

DEFAULT_LOT_STATUS: LotStatus = "available"

_CENTS = Decimal("0.01")


def fine_weight_g(gross_weight_g: Decimal, purity: Decimal) -> Decimal:
    """Peso fino (gramos de metal puro) = peso bruto × pureza (fracción 0–1)."""
    return gross_weight_g * purity


def fine_ounces(gross_weight_g: Decimal, purity: Decimal) -> Decimal:
    """Onzas troy finas contenidas en el peso bruto dado su pureza."""
    return fine_weight_g(gross_weight_g, purity) / TROY_OUNCE_G


def valuation_usd(gross_weight_g: Decimal, purity: Decimal, price_per_oz: Decimal) -> Decimal:
    """Valor en USD del material: onzas finas × precio por onza, a 2 decimales."""
    value = fine_ounces(gross_weight_g, purity) * price_per_oz
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)
