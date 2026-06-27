"""Reglas y vocabulario del dominio de Terceros (Clientes/Proveedores).

Tipos y estados se modelan como literales estables (sin enums runtime) para
mantener una única fuente de verdad compartida por persistencia, API y validación.
"""

from __future__ import annotations

from typing import Literal, get_args

PartyKind = Literal["customer", "supplier"]
"""Discriminador del tercero: cliente o proveedor."""

PartyStatus = Literal["active", "evaluation", "inactive"]
"""Estado comercial del tercero (réplica de los badges de la maqueta)."""

PARTY_KINDS: tuple[PartyKind, ...] = get_args(PartyKind)
PARTY_STATUSES: tuple[PartyStatus, ...] = get_args(PartyStatus)

DEFAULT_PARTY_STATUS: PartyStatus = "active"

# Rango admisible del rating de proveedor (evaluación, sección 7.6).
RATING_MIN = 0.0
RATING_MAX = 5.0


def is_valid_kind(value: str) -> bool:
    return value in PARTY_KINDS


def is_valid_status(value: str) -> bool:
    return value in PARTY_STATUSES
