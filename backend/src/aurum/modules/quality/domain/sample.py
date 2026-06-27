"""Dominio de Calidad: métodos de análisis y resultados (sección 7.5/9)."""

from __future__ import annotations

from typing import Literal, get_args

AnalysisMethod = Literal["cupellation", "xrf", "fire_assay", "gravimetry"]
"""Métodos de laboratorio (Copelación, XRF, Ensayo de fuego, Gravimetría)."""

SampleResult = Literal["pending", "approved", "rejected"]

ANALYSIS_METHODS: tuple[AnalysisMethod, ...] = get_args(AnalysisMethod)
SAMPLE_RESULTS: tuple[SampleResult, ...] = get_args(SampleResult)

DEFAULT_SAMPLE_RESULT: SampleResult = "pending"
