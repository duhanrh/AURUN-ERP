"""Esquemas Pydantic de la API de Contabilidad (sección 7.12)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from aurum.modules.accounting.application.dto import (
    AccountingKpis,
    AccountView,
    BalanceLine,
    BalanceSheetView,
    JournalEntryView,
    NewManualEntry,
    NewManualLine,
    NewPayment,
    PartyBalanceView,
)


class AccountResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    type: str
    normal_balance: str

    @classmethod
    def from_view(cls, v: AccountView) -> AccountResponse:
        return cls(id=v.id, code=v.code, name=v.name, type=v.type, normal_balance=v.normal_balance)


class LedgerLineResponse(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    debit: Decimal
    credit: Decimal
    party_id: uuid.UUID | None
    party_name: str | None


class JournalEntryResponse(BaseModel):
    id: uuid.UUID
    entry_code: str
    entry_date: date
    memo: str
    source_type: str
    source_id: uuid.UUID | None
    total_debit: Decimal
    total_credit: Decimal
    lines: list[LedgerLineResponse]
    created_at: datetime | None

    @classmethod
    def from_view(cls, v: JournalEntryView) -> JournalEntryResponse:
        return cls(
            id=v.id,
            entry_code=v.entry_code,
            entry_date=v.entry_date,
            memo=v.memo,
            source_type=v.source_type,
            source_id=v.source_id,
            total_debit=v.total_debit,
            total_credit=v.total_credit,
            lines=[
                LedgerLineResponse(
                    account_code=line.account_code,
                    account_name=line.account_name,
                    account_type=line.account_type,
                    debit=line.debit,
                    credit=line.credit,
                    party_id=line.party_id,
                    party_name=line.party_name,
                )
                for line in v.lines
            ],
            created_at=v.created_at,
        )


class AccountingKpisResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_income: Decimal
    cash_balance: Decimal
    receivable_total: Decimal
    payable_total: Decimal
    journal_entries: int

    @classmethod
    def from_view(cls, v: AccountingKpis) -> AccountingKpisResponse:
        return cls(
            total_income=v.total_income,
            total_expense=v.total_expense,
            net_income=v.net_income,
            cash_balance=v.cash_balance,
            receivable_total=v.receivable_total,
            payable_total=v.payable_total,
            journal_entries=v.journal_entries,
        )


class BalanceLineResponse(BaseModel):
    code: str
    name: str
    amount: Decimal


class BalanceSheetResponse(BaseModel):
    assets: list[BalanceLineResponse]
    liabilities: list[BalanceLineResponse]
    equity: list[BalanceLineResponse]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    result_for_period: Decimal
    is_balanced: bool

    @classmethod
    def from_view(cls, v: BalanceSheetView) -> BalanceSheetResponse:
        def lines(items: list[BalanceLine]) -> list[BalanceLineResponse]:
            return [BalanceLineResponse(code=i.code, name=i.name, amount=i.amount) for i in items]

        return cls(
            assets=lines(v.assets),
            liabilities=lines(v.liabilities),
            equity=lines(v.equity),
            total_assets=v.total_assets,
            total_liabilities=v.total_liabilities,
            total_equity=v.total_equity,
            result_for_period=v.result_for_period,
            is_balanced=v.is_balanced,
        )


class PartyBalanceResponse(BaseModel):
    party_id: uuid.UUID | None
    party_name: str
    balance: Decimal

    @classmethod
    def from_view(cls, v: PartyBalanceView) -> PartyBalanceResponse:
        return cls(party_id=v.party_id, party_name=v.party_name, balance=v.balance)


# ── Requests ────────────────────────────────────────────────────────────────
class ManualLineRequest(BaseModel):
    account_code: str = Field(min_length=1, max_length=16)
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    party_id: uuid.UUID | None = None
    party_name: str | None = Field(default=None, max_length=200)

    def to_dto(self) -> NewManualLine:
        return NewManualLine(
            account_code=self.account_code,
            debit=self.debit,
            credit=self.credit,
            party_id=self.party_id,
            party_name=self.party_name,
        )


class CreateManualEntryRequest(BaseModel):
    memo: str = Field(min_length=1, max_length=240)
    entry_date: date | None = None
    lines: list[ManualLineRequest] = Field(min_length=2)

    def to_dto(self) -> NewManualEntry:
        return NewManualEntry(
            memo=self.memo,
            entry_date=self.entry_date,
            lines=[line.to_dto() for line in self.lines],
        )


class RegisterPaymentRequest(BaseModel):
    direction: str = Field(pattern="^(inbound|outbound)$")
    party_id: uuid.UUID
    party_name: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    cash_account_code: str = Field(default="1110", max_length=16)
    memo: str | None = Field(default=None, max_length=240)
    paid_at: date | None = None

    def to_dto(self) -> NewPayment:
        return NewPayment(
            direction=self.direction,
            party_id=self.party_id,
            party_name=self.party_name,
            amount=self.amount,
            cash_account_code=self.cash_account_code,
            memo=self.memo,
            paid_at=self.paid_at,
        )
