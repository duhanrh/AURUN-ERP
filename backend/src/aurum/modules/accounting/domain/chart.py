"""Dominio contable: tipos de cuenta y plan de cuentas base (sección 7.12).

El plan de cuentas (``ChartOfAccount``) es la fuente de verdad de las cuentas que
participan en los asientos. Se siembra por tenant en el provisionamiento, igual que
el catálogo de materiales. Las cuentas "bien conocidas" (caja, CxC, inventario,
CxP, ingresos, costo) tienen códigos estables que la lógica de asientos automáticos
referencia por constante, evitando *strings* mágicos dispersos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

AccountType = Literal["asset", "liability", "equity", "income", "expense"]
"""Naturaleza contable de una cuenta."""

NormalBalance = Literal["debit", "credit"]
"""Saldo normal: activos/gastos por débito; pasivos/patrimonio/ingresos por crédito."""

ACCOUNT_TYPES: tuple[AccountType, ...] = get_args(AccountType)
NORMAL_BALANCES: tuple[NormalBalance, ...] = get_args(NormalBalance)

# Saldo normal por tipo de cuenta (regla contable estándar).
NORMAL_BALANCE_BY_TYPE: dict[AccountType, NormalBalance] = {
    "asset": "debit",
    "expense": "debit",
    "liability": "credit",
    "equity": "credit",
    "income": "credit",
}


@dataclass(frozen=True, slots=True)
class AccountDef:
    """Definición inmutable de una cuenta del plan base."""

    code: str
    name: str
    type: AccountType

    @property
    def normal_balance(self) -> NormalBalance:
        return NORMAL_BALANCE_BY_TYPE[self.type]


# ── Códigos estables de cuentas bien conocidas (referenciados por los asientos) ──
ACC_CASH = "1105"  # Caja
ACC_BANK = "1110"  # Bancos
ACC_RECEIVABLE = "1305"  # Cuentas por cobrar (clientes) — subledger por tercero
ACC_INVENTORY = "1435"  # Inventario de metales preciosos
ACC_PAYABLE = "2205"  # Cuentas por pagar (proveedores) — subledger por tercero
ACC_CAPITAL = "3115"  # Capital social
ACC_SALES = "4135"  # Ingresos por venta de metales
ACC_COGS = "6135"  # Costo de la mercancía vendida
ACC_TRANSFORM_COST = "7135"  # Costos de transformación


# ── Plan de cuentas base sembrado en cada tenant nuevo (sección 5.7) ──
BASE_ACCOUNTS: tuple[AccountDef, ...] = (
    AccountDef(ACC_CASH, "Caja", "asset"),
    AccountDef(ACC_BANK, "Bancos", "asset"),
    AccountDef(ACC_RECEIVABLE, "Cuentas por Cobrar", "asset"),
    AccountDef(ACC_INVENTORY, "Inventario de Metales", "asset"),
    AccountDef(ACC_PAYABLE, "Cuentas por Pagar", "liability"),
    AccountDef(ACC_CAPITAL, "Capital Social", "equity"),
    AccountDef(ACC_SALES, "Ingresos por Venta", "income"),
    AccountDef(ACC_COGS, "Costo de Ventas", "expense"),
    AccountDef(ACC_TRANSFORM_COST, "Costos de Transformación", "expense"),
)

ACCOUNT_BY_CODE: dict[str, AccountDef] = {a.code: a for a in BASE_ACCOUNTS}
