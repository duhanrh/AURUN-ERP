"""Pruebas unitarias del dominio del pipeline de transformación (sección 7.4)."""

from __future__ import annotations

from decimal import Decimal

from aurum.modules.transformation.domain.pipeline import (
    FIRST_STAGE,
    LAST_STAGE,
    STAGE_ORDER,
    next_stage,
    output_weight_g,
)


def test_pipeline_has_five_ordered_stages() -> None:
    assert STAGE_ORDER == ("reception", "analysis", "melting", "refining", "certified")
    assert FIRST_STAGE == "reception"
    assert LAST_STAGE == "certified"


def test_next_stage_walks_forward_then_stops() -> None:
    assert next_stage("reception") == "analysis"
    assert next_stage("refining") == "certified"
    assert next_stage("certified") is None


def test_output_weight_applies_yield() -> None:
    assert output_weight_g(Decimal("400"), Decimal("0.95")) == Decimal("380.0000")


def test_output_weight_of_perfect_yield_is_input() -> None:
    assert output_weight_g(Decimal("100"), Decimal("1")) == Decimal("100.0000")
