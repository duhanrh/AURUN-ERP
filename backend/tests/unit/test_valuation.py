"""Pruebas unitarias del dominio de valorización del Inventario (sección 7.1)."""

from __future__ import annotations

from decimal import Decimal

from aurum.modules.inventory.domain.valuation import (
    TROY_OUNCE_G,
    fine_ounces,
    fine_weight_g,
    valuation_usd,
)


def test_fine_weight_is_gross_times_purity() -> None:
    assert fine_weight_g(Decimal("1000"), Decimal("0.75")) == Decimal("750.00")


def test_one_troy_ounce_of_pure_metal_is_one_fine_ounce() -> None:
    assert fine_ounces(TROY_OUNCE_G, Decimal("1")) == Decimal("1")


def test_valuation_rounds_to_cents() -> None:
    # 1 oz troy de metal puro a $3000/oz = $3000.00 exacto.
    assert valuation_usd(TROY_OUNCE_G, Decimal("1"), Decimal("3000")) == Decimal("3000.00")


def test_valuation_scales_with_weight_purity_and_price() -> None:
    # 2 oz troy al 50% de pureza a $1000/oz = 1 oz fina × $1000 = $1000.00.
    value = valuation_usd(TROY_OUNCE_G * 2, Decimal("0.5"), Decimal("1000"))
    assert value == Decimal("1000.00")


def test_zero_weight_is_zero_value() -> None:
    assert valuation_usd(Decimal("0"), Decimal("0.999"), Decimal("3000")) == Decimal("0.00")
