"""Vocabulario y reglas de la Orden de Venta (sección 7.3)."""

from __future__ import annotations

from typing import Literal, get_args

SalesOrderStatus = Literal["pending_payment", "preparing", "completed", "cancelled"]

SALES_ORDER_STATUSES: tuple[SalesOrderStatus, ...] = get_args(SalesOrderStatus)

DEFAULT_SALES_ORDER_STATUS: SalesOrderStatus = "pending_payment"

# Estados terminales: no admiten más transiciones.
TERMINAL_STATUSES: tuple[SalesOrderStatus, ...] = ("completed", "cancelled")
