"""Dominio de Transformación: pipeline de etapas, procesos y rendimiento (7.4).

El pipeline de 5 etapas (Recepción → Análisis → Fundición → Refinado → Certificado)
es la fuente de verdad tanto del backend como del componente visual del frontend.
El rendimiento (yield) relaciona el peso de salida con el de entrada.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, get_args

Stage = Literal["reception", "analysis", "melting", "refining", "certified"]
"""Etapas ordenadas del pipeline de transformación."""

TransformationStatus = Literal["in_progress", "completed", "cancelled"]

Process = Literal["acid_refining", "melting_alloy", "rolling", "granulation", "purification"]
"""Procesos de transformación (sección 9 de la maqueta)."""

# Orden canónico del pipeline; ``advance`` avanza al siguiente.
STAGE_ORDER: tuple[Stage, ...] = get_args(Stage)
PROCESSES: tuple[Process, ...] = get_args(Process)
TRANSFORMATION_STATUSES: tuple[TransformationStatus, ...] = get_args(TransformationStatus)

FIRST_STAGE: Stage = STAGE_ORDER[0]
LAST_STAGE: Stage = STAGE_ORDER[-1]


def next_stage(stage: Stage) -> Stage | None:
    """Devuelve la etapa siguiente, o ``None`` si ya es la última."""
    idx = STAGE_ORDER.index(stage)
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None


def output_weight_g(input_weight_g: Decimal, yield_fraction: Decimal) -> Decimal:
    """Peso de salida esperado = peso de entrada × rendimiento (fracción 0–1)."""
    return (input_weight_g * yield_fraction).quantize(Decimal("0.0001"))
