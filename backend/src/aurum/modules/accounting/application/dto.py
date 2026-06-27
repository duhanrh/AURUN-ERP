"""DTOs del módulo de Contabilidad (independientes del ORM)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from aurum.modules.accounting.domain.chart import AccountType, NormalBalance


@dataclass(frozen=True, slots=True)
class AccountView:
    id: uuid.UUID
    code: str
    name: str
    type: AccountType
    normal_balance: NormalBalance


@dataclass(frozen=True, slots=True)
class LedgerLineView:
    account_code: str
    account_name: str
    account_type: AccountType
    debit: Decimal
    credit: Decimal
    party_id: uuid.UUID | None
    party_name: str | None


@dataclass(frozen=True, slots=True)
class JournalEntryView:
    id: uuid.UUID
    entry_code: str
    entry_date: date
    memo: str
    source_type: str
    source_id: uuid.UUID | None
    total_debit: Decimal
    total_credit: Decimal
    lines: list[LedgerLineView]
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class AccountingKpis:
    total_income: Decimal
    total_expense: Decimal
    net_income: Decimal
    cash_balance: Decimal
    receivable_total: Decimal
    payable_total: Decimal
    journal_entries: int


@dataclass(frozen=True, slots=True)
class BalanceLine:
    code: str
    name: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class BalanceSheetView:
    assets: list[BalanceLine]
    liabilities: list[BalanceLine]
    equity: list[BalanceLine]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    result_for_period: Decimal
    is_balanced: bool


@dataclass(frozen=True, slots=True)
class PartyBalanceView:
    party_id: uuid.UUID | None
    party_name: str
    balance: Decimal


# ── Entradas (asiento manual) ──
@dataclass(frozen=True, slots=True)
class NewManualLine:
    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    party_id: uuid.UUID | None = None
    party_name: str | None = None


@dataclass(frozen=True, slots=True)
class NewManualEntry:
    memo: str
    lines: list[NewManualLine]
    entry_date: date | None = None


# ── Entradas (pago de tesorería) ──
@dataclass(frozen=True, slots=True)
class NewPayment:
    direction: str  # "inbound" (cobro de cliente) | "outbound" (pago a proveedor)
    party_id: uuid.UUID
    party_name: str
    amount: Decimal
    cash_account_code: str = "1110"  # Bancos por defecto
    memo: str | None = None
    paid_at: date | None = None


# ── Datos para asientos automáticos (los arma el servicio que opera el negocio) ──
# (los consumen Compras y Ventas al llamar a AccountingService)
@dataclass(frozen=True, slots=True)
class PurchasePosting:
    supplier_id: uuid.UUID
    supplier_name: str
    amount: Decimal
    source_id: uuid.UUID
    source_code: str


@dataclass(frozen=True, slots=True)
class SalePosting:
    customer_id: uuid.UUID
    customer_name: str
    revenue: Decimal
    cost: Decimal
    source_id: uuid.UUID
    source_code: str
