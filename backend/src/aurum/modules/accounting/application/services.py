"""Casos de uso de Contabilidad y Tesorería (secciones 7.12 / 7.13).

Este servicio concentra **toda** la lógica contable, de modo que otros módulos
(Compras, Ventas) solo le entregan datos del negocio y él decide qué cuentas
afecta cada operación. Así la lógica de partida doble no queda dispersa.

Invariante central (criterio de aceptación de la Fase 6): todo asiento se valida
balanceado (Σdébitos = Σcréditos) antes de persistirse. El Balance General es una
proyección de lectura sobre las líneas, nunca una tabla mantenida en paralelo.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from aurum.modules.accounting.application.dto import (
    AccountingKpis,
    AccountView,
    BalanceLine,
    BalanceSheetView,
    JournalEntryView,
    LedgerLineView,
    NewManualEntry,
    NewManualLine,
    NewPayment,
    PartyBalanceView,
    PurchasePosting,
    SalePosting,
)
from aurum.modules.accounting.application.ports import (
    AccountRepository,
    JournalEntryRepository,
)
from aurum.modules.accounting.domain.chart import (
    ACC_BANK,
    ACC_CASH,
    ACC_COGS,
    ACC_INVENTORY,
    ACC_PAYABLE,
    ACC_RECEIVABLE,
    ACC_SALES,
    NormalBalance,
)
from aurum.modules.accounting.domain.posting import (
    PostingLine,
    is_balanced,
    total_credit,
    total_debit,
)
from aurum.modules.accounting.infrastructure.models import (
    ChartAccount,
    JournalEntry,
    LedgerEntry,
)
from aurum.shared.codes import generate_code
from aurum.shared.errors import ConflictError, DomainError, NotFoundError

CENTS = Decimal("0.01")


class UnbalancedEntryError(DomainError):
    status_code = 422
    error_code = "unbalanced_entry"


class AccountingService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        accounts: AccountRepository,
        journals: JournalEntryRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._accounts = accounts
        self._journals = journals
        self._account_cache: dict[str, ChartAccount] = {}

    # ── Consultas ──────────────────────────────────────────────────────────
    async def list_accounts(self) -> list[AccountView]:
        return [_account_to_view(a) for a in await self._accounts.list_all()]

    async def list_entries(self) -> list[JournalEntryView]:
        return [_entry_to_view(e) for e in await self._journals.list_all()]

    async def kpis(self) -> AccountingKpis:
        entries = await self._journals.list_all()
        balances = _account_balances(entries)
        accounts = {a.code: a for a in await self._accounts.list_all()}
        income = Decimal("0")
        expense = Decimal("0")
        for code, acc in accounts.items():
            natural = _natural_amount(
                balances.get(code, Decimal("0")),
                acc.normal_balance,  # type: ignore[arg-type]
            )
            if acc.type == "income":
                income += natural
            elif acc.type == "expense":
                expense += natural
        cash = balances.get(ACC_CASH, Decimal("0")) + balances.get(ACC_BANK, Decimal("0"))
        receivable = max(balances.get(ACC_RECEIVABLE, Decimal("0")), Decimal("0"))
        payable = -min(balances.get(ACC_PAYABLE, Decimal("0")), Decimal("0"))
        return AccountingKpis(
            total_income=income.quantize(CENTS),
            total_expense=expense.quantize(CENTS),
            net_income=(income - expense).quantize(CENTS),
            cash_balance=cash.quantize(CENTS),
            receivable_total=receivable.quantize(CENTS),
            payable_total=payable.quantize(CENTS),
            journal_entries=len(entries),
        )

    async def balance_sheet(self) -> BalanceSheetView:
        entries = await self._journals.list_all()
        signed = _account_balances(entries)  # saldo deudor (positivo = débito neto)
        accounts = {a.code: a for a in await self._accounts.list_all()}

        assets: list[BalanceLine] = []
        liabilities: list[BalanceLine] = []
        equity: list[BalanceLine] = []
        income = Decimal("0")
        expense = Decimal("0")

        for code, acc in sorted(accounts.items()):
            raw = signed.get(code, Decimal("0"))
            natural = _natural_amount(raw, acc.normal_balance)  # type: ignore[arg-type]
            if acc.type == "asset":
                if natural != 0:
                    assets.append(BalanceLine(code, acc.name, natural))
            elif acc.type == "liability":
                if natural != 0:
                    liabilities.append(BalanceLine(code, acc.name, natural))
            elif acc.type == "equity":
                if natural != 0:
                    equity.append(BalanceLine(code, acc.name, natural))
            elif acc.type == "income":
                income += natural
            elif acc.type == "expense":
                expense += natural

        result = (income - expense).quantize(CENTS)
        # La utilidad del ejercicio cierra contra patrimonio (ecuación contable).
        equity.append(BalanceLine("3605", "Resultado del Ejercicio", result))

        total_assets = sum((line.amount for line in assets), Decimal("0")).quantize(CENTS)
        total_liabilities = sum((line.amount for line in liabilities), Decimal("0")).quantize(CENTS)
        total_equity = sum((line.amount for line in equity), Decimal("0")).quantize(CENTS)
        return BalanceSheetView(
            assets=assets,
            liabilities=liabilities,
            equity=equity,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            result_for_period=result,
            is_balanced=total_assets == (total_liabilities + total_equity),
        )

    async def receivables(self) -> list[PartyBalanceView]:
        return await self._subledger(ACC_RECEIVABLE, normal="debit")

    async def payables(self) -> list[PartyBalanceView]:
        return await self._subledger(ACC_PAYABLE, normal="credit")

    async def _subledger(
        self, account_code: str, *, normal: NormalBalance
    ) -> list[PartyBalanceView]:
        entries = await self._journals.list_all()
        by_party: dict[uuid.UUID | None, tuple[str, Decimal]] = {}
        for entry in entries:
            for line in entry.lines:
                if line.account is None or line.account.code != account_code:
                    continue
                signed = line.debit - line.credit  # deudor positivo
                amount = signed if normal == "debit" else -signed
                name, acc = by_party.get(line.party_id, ("", Decimal("0")))
                by_party[line.party_id] = (line.party_name or name or "—", acc + amount)
        result = [
            PartyBalanceView(party_id=pid, party_name=name, balance=balance.quantize(CENTS))
            for pid, (name, balance) in by_party.items()
            if balance.quantize(CENTS) != 0
        ]
        result.sort(key=lambda r: r.balance, reverse=True)
        return result

    # ── Asientos automáticos desde la operación ────────────────────────────
    async def record_purchase(self, data: PurchasePosting) -> JournalEntryView:
        """Compra aprobada: Dr Inventario / Cr Cuentas por Pagar (proveedor)."""
        lines = [
            PostingLine(ACC_INVENTORY, debit=data.amount),
            PostingLine(
                ACC_PAYABLE,
                credit=data.amount,
                party_id=data.supplier_id,
                party_name=data.supplier_name,
            ),
        ]
        return await self._post(
            memo=f"Compra {data.source_code} — {data.supplier_name}",
            source_type="purchase",
            source_id=data.source_id,
            lines=lines,
        )

    async def record_sale(self, data: SalePosting) -> JournalEntryView:
        """Venta: Dr CxC / Cr Ingresos + Dr Costo de Ventas / Cr Inventario."""
        lines = [
            PostingLine(
                ACC_RECEIVABLE,
                debit=data.revenue,
                party_id=data.customer_id,
                party_name=data.customer_name,
            ),
            PostingLine(ACC_SALES, credit=data.revenue),
            PostingLine(ACC_COGS, debit=data.cost),
            PostingLine(ACC_INVENTORY, credit=data.cost),
        ]
        return await self._post(
            memo=f"Venta {data.source_code} — {data.customer_name}",
            source_type="sale",
            source_id=data.source_id,
            lines=lines,
        )

    async def reverse_sale(self, data: SalePosting) -> JournalEntryView:
        """Cancelación de venta: reversa exacta del asiento de venta."""
        lines = [
            PostingLine(ACC_SALES, debit=data.revenue),
            PostingLine(
                ACC_RECEIVABLE,
                credit=data.revenue,
                party_id=data.customer_id,
                party_name=data.customer_name,
            ),
            PostingLine(ACC_INVENTORY, debit=data.cost),
            PostingLine(ACC_COGS, credit=data.cost),
        ]
        return await self._post(
            memo=f"Reversa venta {data.source_code} — {data.customer_name}",
            source_type="sale_reversal",
            source_id=data.source_id,
            lines=lines,
        )

    # ── Tesorería: pagos (cobros/pagos) ────────────────────────────────────
    async def register_payment(self, data: NewPayment) -> JournalEntryView:
        amount = data.amount.quantize(CENTS)
        if amount <= 0:
            raise ConflictError("El monto del pago debe ser mayor que cero.")
        if data.direction == "inbound":
            # Cobro de cliente: Dr Caja/Bancos / Cr CxC.
            lines = [
                PostingLine(data.cash_account_code, debit=amount),
                PostingLine(
                    ACC_RECEIVABLE,
                    credit=amount,
                    party_id=data.party_id,
                    party_name=data.party_name,
                ),
            ]
            memo = data.memo or f"Cobro — {data.party_name}"
        elif data.direction == "outbound":
            # Pago a proveedor: Dr CxP / Cr Caja/Bancos.
            lines = [
                PostingLine(
                    ACC_PAYABLE,
                    debit=amount,
                    party_id=data.party_id,
                    party_name=data.party_name,
                ),
                PostingLine(data.cash_account_code, credit=amount),
            ]
            memo = data.memo or f"Pago — {data.party_name}"
        else:
            raise ConflictError("Dirección de pago inválida (inbound|outbound).")
        return await self._post(
            memo=memo,
            source_type="payment",
            source_id=None,
            lines=lines,
            entry_date=data.paid_at,
        )

    # ── Asiento manual ─────────────────────────────────────────────────────
    async def create_manual_entry(self, data: NewManualEntry) -> JournalEntryView:
        if len(data.lines) < 2:
            raise ConflictError("Un asiento requiere al menos dos líneas.")
        lines = [_manual_to_posting(line) for line in data.lines]
        return await self._post(
            memo=data.memo,
            source_type="manual",
            source_id=None,
            lines=lines,
            entry_date=data.entry_date,
        )

    # ── Núcleo de posteo ───────────────────────────────────────────────────
    async def _post(
        self,
        *,
        memo: str,
        source_type: str,
        source_id: uuid.UUID | None,
        lines: list[PostingLine],
        entry_date: date | None = None,
    ) -> JournalEntryView:
        if not is_balanced(lines):
            raise UnbalancedEntryError(
                f"Asiento desbalanceado: débitos {total_debit(lines)} ≠ "
                f"créditos {total_credit(lines)}."
            )
        entry = JournalEntry(
            tenant_id=self._tenant_id,
            entry_code=generate_code("AS"),
            entry_date=entry_date or date.today(),
            memo=memo,
            source_type=source_type,
            source_id=source_id,
        )
        for line in lines:
            account = await self._resolve_account(line.account_code)
            entry.lines.append(
                LedgerEntry(
                    tenant_id=self._tenant_id,
                    account_id=account.id,
                    debit=line.debit.quantize(CENTS),
                    credit=line.credit.quantize(CENTS),
                    party_id=line.party_id,
                    party_name=line.party_name,
                )
            )
        await self._journals.add(entry)
        stored = await self._journals.get(entry.id)
        assert stored is not None
        return _entry_to_view(stored)

    async def _resolve_account(self, code: str) -> ChartAccount:
        if code not in self._account_cache:
            account = await self._accounts.get_by_code(code)
            if account is None:
                raise NotFoundError(f"Cuenta contable '{code}' no existe en el plan.")
            self._account_cache[code] = account
        return self._account_cache[code]


# ── Helpers de proyección ──────────────────────────────────────────────────
def _account_to_view(a: ChartAccount) -> AccountView:
    return AccountView(
        id=a.id,
        code=a.code,
        name=a.name,
        type=a.type,  # type: ignore[arg-type]
        normal_balance=a.normal_balance,  # type: ignore[arg-type]
    )


def _line_to_view(line: LedgerEntry) -> LedgerLineView:
    acc = line.account
    return LedgerLineView(
        account_code=acc.code if acc else "—",
        account_name=acc.name if acc else "—",
        account_type=acc.type if acc else "asset",  # type: ignore[arg-type]
        debit=line.debit,
        credit=line.credit,
        party_id=line.party_id,
        party_name=line.party_name,
    )


def _entry_to_view(entry: JournalEntry) -> JournalEntryView:
    debit = sum((line.debit for line in entry.lines), Decimal("0")).quantize(CENTS)
    credit = sum((line.credit for line in entry.lines), Decimal("0")).quantize(CENTS)
    return JournalEntryView(
        id=entry.id,
        entry_code=entry.entry_code,
        entry_date=entry.entry_date,
        memo=entry.memo,
        source_type=entry.source_type,
        source_id=entry.source_id,
        total_debit=debit,
        total_credit=credit,
        lines=[_line_to_view(line) for line in entry.lines],
        created_at=entry.created_at,
    )


def _account_balances(entries: list[JournalEntry]) -> dict[str, Decimal]:
    """Saldo deudor neto por código de cuenta (débitos − créditos)."""
    balances: dict[str, Decimal] = {}
    for entry in entries:
        for line in entry.lines:
            if line.account is None:
                continue
            code = line.account.code
            balances[code] = balances.get(code, Decimal("0")) + line.debit - line.credit
    return balances


def _natural_amount(signed_debit_balance: Decimal, normal: NormalBalance) -> Decimal:
    """Convierte el saldo deudor neto al signo natural de la cuenta."""
    value = signed_debit_balance if normal == "debit" else -signed_debit_balance
    return value.quantize(CENTS)


def _manual_to_posting(line: NewManualLine) -> PostingLine:
    return PostingLine(
        account_code=line.account_code,
        debit=line.debit,
        credit=line.credit,
        party_id=line.party_id,
        party_name=line.party_name,
    )
