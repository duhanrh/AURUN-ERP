"""Casos de uso de Ventas: alta de OV con consumo de stock y transiciones (7.3).

Crear una OV descuenta el peso vendido del lote (no puede exceder lo disponible).
Cancelar una OV restituye ese peso al lote. La valorización usa la pureza real del
lote vendido (``peso × pureza × precio``).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from aurum.modules.accounting.application.dto import SalePosting
from aurum.modules.accounting.application.services import AccountingService
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.domain.valuation import valuation_usd
from aurum.modules.sales.application.dto import (
    NewSalesOrder,
    SalesKpis,
    SalesOrderPatch,
    SalesOrderView,
)
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
        is_deleted=order.deleted_at is not None,
    )


class SalesService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        orders: SalesOrderRepository,
        inventory: InventoryService,
        customers: PartyRepository,
        accounting: AccountingService,
    ) -> None:
        self._tenant_id = tenant_id
        self._orders = orders
        self._inventory = inventory
        self._customers = customers
        self._accounting = accounting

    async def list_orders(self, *, include_deleted: bool = False) -> list[SalesOrderView]:
        return [_to_view(o) for o in await self._orders.list_all(include_deleted=include_deleted)]

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
        customer = await self._customers.get("customer", data.customer_id)
        if customer is None:
            raise NotFoundError("Cliente no encontrado.")

        # Consume el stock del lote: valida existencia y disponibilidad (puede
        # lanzar InsufficientStockError). El descuento queda en la misma transacción.
        lot = await self._inventory.consume_lot(data.lot_id, data.quantity_g)

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

        # Asiento automático: Dr CxC / Cr Ingresos + Dr Costo de Ventas / Cr Inventario.
        # El ingreso usa el precio de venta; el costo, el precio del lote (base de costo).
        revenue = valuation_usd(data.quantity_g, lot.declared_purity, data.price_per_oz)
        cost = valuation_usd(data.quantity_g, lot.declared_purity, lot.price_per_oz)
        await self._accounting.record_sale(
            SalePosting(
                customer_id=data.customer_id,
                customer_name=customer.legal_name,
                revenue=revenue,
                cost=cost,
                source_id=created.id,
                source_code=created.order_code,
            )
        )
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
            # Restituye el stock vendido al lote y reversa el asiento contable.
            await self._inventory.restore_lot(order.lot_id, order.quantity_g)
            purity = order.lot.declared_purity if order.lot else Decimal("0")
            lot_cost = order.lot.price_per_oz if order.lot else Decimal("0")
            await self._accounting.reverse_sale(
                SalePosting(
                    customer_id=order.customer_id,
                    customer_name=order.customer.legal_name if order.customer else "—",
                    revenue=valuation_usd(order.quantity_g, purity, order.price_per_oz),
                    cost=valuation_usd(order.quantity_g, purity, lot_cost),
                    source_id=order.id,
                    source_code=order.order_code,
                )
            )
        order.status = new_status
        return _to_view(order)

    async def update_order(self, order_id: uuid.UUID, patch: SalesOrderPatch) -> SalesOrderView:
        order = await self._require(order_id)
        if order.status != "pending_payment":
            raise ConflictError(
                f"Sólo se puede editar una OV pendiente de pago (estado: {order.status})."
            )
        if "price_per_oz" in patch.fields_set and patch.price_per_oz is not None:
            order.price_per_oz = patch.price_per_oz
        if "invoice_number" in patch.fields_set:
            order.invoice_number = patch.invoice_number
        return _to_view(order)

    async def delete_order(self, order_id: uuid.UUID) -> SalesOrderView:
        order = await self._require(order_id)
        if order.status != "cancelled":
            raise ConflictError(
                "Sólo se puede eliminar una OV cancelada (cancelar antes restituye stock "
                "y reversa el asiento)."
            )
        order.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return _to_view(order)

    async def restore_order(self, order_id: uuid.UUID) -> SalesOrderView:
        order = await self._orders.get(order_id, include_deleted=True)
        if order is None:
            raise NotFoundError("Orden de venta no encontrada.")
        if order.deleted_at is None:
            raise ConflictError("La OV no está eliminada.")
        order.deleted_at = None
        return _to_view(order)

    async def _require(self, order_id: uuid.UUID) -> SalesOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de venta no encontrada.")
        return order
