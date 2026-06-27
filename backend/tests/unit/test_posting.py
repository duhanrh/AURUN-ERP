"""Pruebas unitarias de la invariante de partida doble (Fase 6, sección 7.12).

La regla contable central —Σdébitos = Σcréditos por asiento— se valida en el
dominio puro, sin tocar la base de datos.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from aurum.modules.accounting.domain.chart import (
    ACC_INVENTORY,
    ACC_PAYABLE,
    ACC_RECEIVABLE,
    ACC_SALES,
    NORMAL_BALANCE_BY_TYPE,
)
from aurum.modules.accounting.domain.posting import (
    PostingLine,
    is_balanced,
    total_credit,
    total_debit,
)


def test_balanced_two_line_entry() -> None:
    lines = [
        PostingLine(ACC_INVENTORY, debit=Decimal("1000.00")),
        PostingLine(ACC_PAYABLE, credit=Decimal("1000.00")),
    ]
    assert is_balanced(lines)
    assert total_debit(lines) == Decimal("1000.00")
    assert total_credit(lines) == Decimal("1000.00")


def test_balanced_multi_line_sale_entry() -> None:
    # Venta: Dr CxC / Cr Ingresos + Dr Costo / Cr Inventario.
    lines = [
        PostingLine(ACC_RECEIVABLE, debit=Decimal("640.00")),
        PostingLine(ACC_SALES, credit=Decimal("640.00")),
        PostingLine(ACC_INVENTORY, credit=Decimal("490.00")),
        PostingLine("6135", debit=Decimal("490.00")),
    ]
    assert is_balanced(lines)
    assert total_debit(lines) == total_credit(lines) == Decimal("1130.00")


def test_unbalanced_entry_detected() -> None:
    lines = [
        PostingLine(ACC_INVENTORY, debit=Decimal("1000.00")),
        PostingLine(ACC_PAYABLE, credit=Decimal("999.99")),
    ]
    assert not is_balanced(lines)


def test_rounding_to_cents_keeps_balance() -> None:
    lines = [
        PostingLine(ACC_RECEIVABLE, debit=Decimal("33.333")),
        PostingLine(ACC_SALES, credit=Decimal("33.334")),
    ]
    # Ambos redondean a 33.33 → balanceado a centavos.
    assert is_balanced(lines)


def test_party_metadata_optional() -> None:
    line = PostingLine(ACC_RECEIVABLE, debit=Decimal("10"), party_id=uuid.uuid4(), party_name="X")
    assert line.party_name == "X"
    assert NORMAL_BALANCE_BY_TYPE["asset"] == "debit"
    assert NORMAL_BALANCE_BY_TYPE["income"] == "credit"
