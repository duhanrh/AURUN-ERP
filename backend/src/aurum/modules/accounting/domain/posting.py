"""Dominio de la partida doble: líneas de asiento y la invariante débito = crédito.

Este módulo es puro (sin ORM ni IO) y concentra la **invariante contable** que la
Fase 6 exige probar automáticamente: en todo asiento, la suma de débitos debe ser
exactamente igual a la suma de créditos. Se valida aquí (dominio), no solo en la UI.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

CENTS = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PostingLine:
    """Línea de un asiento: afecta una cuenta por débito **o** por crédito.

    ``party_id``/``party_name`` se rellenan solo en las líneas de CxC/CxP para
    alimentar el submayor por tercero (cartera).
    """

    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    party_id: uuid.UUID | None = None
    party_name: str | None = None


def total_debit(lines: list[PostingLine]) -> Decimal:
    return sum((line.debit for line in lines), Decimal("0")).quantize(CENTS)


def total_credit(lines: list[PostingLine]) -> Decimal:
    return sum((line.credit for line in lines), Decimal("0")).quantize(CENTS)


def is_balanced(lines: list[PostingLine]) -> bool:
    """``True`` si la suma de débitos iguala la de créditos (a centavos)."""
    return total_debit(lines) == total_credit(lines)
