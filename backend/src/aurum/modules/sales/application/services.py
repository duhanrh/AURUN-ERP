"""Casos de uso de Ventas: alta de OV con consumo de stock y transiciones (7.3).

Crear una OV descuenta el peso vendido del lote (no puede exceder lo disponible).
Cancelar una OV restituye ese peso al lote. La valorización usa la pureza real del
lote vendido (``peso × pureza × precio``).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.domain.valuation import valuation_usd
from aurum.modules.sales.application.dto import NewSalesOrder, SalesKpis, SalesOrderView
from aurum.modules.sales.application.ports import SalesOrderRepository
from aurum.modules.sales.domain.order import TERMINAL_STATUSES
from aurum.modules.sales.infrastructure.models import SalesOrder
from aurum.modules.terceros.application.ports import PartyRepository
from aurum.shared.codes import generate_code
from aurum.shared.errors import ConflictError, NotFoundError


def _to_view(order: SalesOrder) -> SalesOrderView:
    purity = order.lot.declared_purity if order.lot else Decimal("0")
    return SalesOrderView(
        id=order.id,
        order_code=order.order_code,
        customer_id=order.customer_id,
        customer_name=order.customer.legal_name if order.customer else "—",
        lot_id=order.lot_id,
        lot_code=order.lot.lot_code if order.lot else "—",
        material_name=order.lot.material.name if order.lot and order.lot.material else "—",
        declared_purity=purity,
        quantity_g=order.quantity_g,
        price_per_oz=order.price_per_oz,
        total_usd=valuation_usd(order.quantity_g, purity, order.price_per_oz),
        status=order.status,  # type: ignore[arg-type]
        invoice_number=order.invoice_number,
        created_at=order.created_at,
    )


class SalesService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        orders: SalesOrderRepository,
        inventory: InventoryService,
        customers: PartyRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._orders = orders
        self._inventory = inventory
        self._customers = customers

    async def list_orders(self) -> list[SalesOrderView]:
        return [_to_view(o) for o in await self._orders.list_all()]

    async def get_order(self, order_id: uuid.UUID) -> SalesOrderView:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de venta no encontrada.")
        return _to_view(order)

    async def kpis(self) -> SalesKpis:
        orders = await self._orders.list_all()
        billable = [o for o in orders if o.status != "cancelled"]
        total = sum(
            (
                valuation_usd(
                    o.quantity_g,
                    o.lot.declared_purity if o.lot else Decimal("0"),
                    o.price_per_oz,
                )
                for o in billable
            ),
            Decimal("0"),
        )
        return SalesKpis(
            total_orders=len(orders),
            pending_payment=sum(1 for o in orders if o.status == "pending_payment"),
            completed=sum(1 for o in orders if o.status == "completed"),
            total_amount_usd=total,
        )

    async def create_order(self, data: NewSalesOrder) -> SalesOrderView:
        if await self._customers.get("customer", data.customer_id) is None:
            raise NotFoundError("Cliente no encontrado.")

        # Consume el stock del lote: valida existencia y disponibilidad (puede
        # lanzar InsufficientStockError). El descuento queda en la misma transacción.
        await self._inventory.consume_lot(data.lot_id, data.quantity_g)

        order = SalesOrder(
            tenant_id=self._tenant_id,
            order_code=generate_code("OV"),
            customer_id=data.customer_id,
            lot_id=data.lot_id,
            quantity_g=data.quantity_g,
            price_per_oz=data.price_per_oz,
            invoice_number=data.invoice_number,
        )
        await self._orders.add(order)
        created = await self._orders.get(order.id)
        assert created is not None
        return _to_view(created)

    async def set_status(self, order_id: uuid.UUID, new_status: str) -> SalesOrderView:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de venta no encontrada.")
        if order.status in TERMINAL_STATUSES:
            raise ConflictError(
                f"La orden ya está en estado terminal ({order.status}); no admite cambios."
            )
        if new_status == "cancelled":
            # Restituye el stock vendido al lote.
            await self._inventory.restore_lot(order.lot_id, order.quantity_g)
        order.status = new_status
        return _to_view(order)
