"""Vocabulario y reglas de la Orden de Compra (sección 7.2)."""

from __future__ import annotations

from typing import Literal, get_args

PurchaseOrderStatus = Literal["pending_approval", "approved", "rejected", "cancelled"]

PURCHASE_ORDER_STATUSES: tuple[PurchaseOrderStatus, ...] = get_args(PurchaseOrderStatus)

DEFAULT_PURCHASE_ORDER_STATUS: PurchaseOrderStatus = "pending_approval"

# Sólo una OC pendiente puede aprobarse o rechazarse.
APPROVABLE_FROM: PurchaseOrderStatus = "pending_approval"
