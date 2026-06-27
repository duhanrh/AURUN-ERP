"""Casos de uso de Compras: alta de OC y flujo de aprobación → lote (sección 7.2).

La aprobación es el punto donde Compras alimenta el Inventario: genera un lote con
los términos pactados y lo enlaza a la OC. Sólo una OC ``pending_approval`` puede
aprobarse o rechazarse (invariante de estado).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from aurum.modules.accounting.application.dto import PurchasePosting
from aurum.modules.accounting.application.services import AccountingService
from aurum.modules.inventory.application.dto import NewLot
from aurum.modules.inventory.application.ports import MaterialRepository
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.domain.valuation import valuation_usd
from aurum.modules.purchasing.application.dto import (
    NewPurchaseOrder,
    PurchaseOrderView,
    PurchasingKpis,
)
from aurum.modules.purchasing.application.ports import PurchaseOrderRepository
from aurum.modules.purchasing.domain.order import APPROVABLE_FROM
from aurum.modules.purchasing.infrastructure.models import PurchaseOrder
from aurum.modules.terceros.application.ports import PartyRepository
from aurum.shared.codes import generate_code
from aurum.shared.errors import ConflictError, NotFoundError


def _to_view(order: PurchaseOrder) -> PurchaseOrderView:
    return PurchaseOrderView(
        id=order.id,
        order_code=order.order_code,
        supplier_id=order.supplier_id,
        supplier_name=order.supplier.legal_name if order.supplier else "—",
        material_id=order.material_id,
        material_name=order.material.name if order.material else "—",
        quantity_g=order.quantity_g,
        declared_purity=order.declared_purity,
        form=order.form,  # type: ignore[arg-type]
        price_per_oz=order.price_per_oz,
        total_usd=valuation_usd(order.quantity_g, order.declared_purity, order.price_per_oz),
        location=order.location,
        expected_delivery=order.expected_delivery,
        status=order.status,  # type: ignore[arg-type]
        lot_id=order.lot_id,
        created_at=order.created_at,
    )


class PurchasingService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        orders: PurchaseOrderRepository,
        inventory: InventoryService,
        materials: MaterialRepository,
        suppliers: PartyRepository,
        accounting: AccountingService,
    ) -> None:
        self._tenant_id = tenant_id
        self._orders = orders
        self._inventory = inventory
        self._materials = materials
        self._suppliers = suppliers
        self._accounting = accounting

    async def list_orders(self) -> list[PurchaseOrderView]:
        return [_to_view(o) for o in await self._orders.list_all()]

    async def get_order(self, order_id: uuid.UUID) -> PurchaseOrderView:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de compra no encontrada.")
        return _to_view(order)

    async def kpis(self) -> PurchasingKpis:
        orders = await self._orders.list_all()
        active = [o for o in orders if o.status not in ("cancelled", "rejected")]
        total = sum(
            (valuation_usd(o.quantity_g, o.declared_purity, o.price_per_oz) for o in active),
            Decimal("0"),
        )
        return PurchasingKpis(
            total_orders=len(orders),
            pending_approval=sum(1 for o in orders if o.status == "pending_approval"),
            approved=sum(1 for o in orders if o.status == "approved"),
            total_amount_usd=total,
        )

    async def create_order(self, data: NewPurchaseOrder) -> PurchaseOrderView:
        if await self._materials.get(data.material_id) is None:
            raise NotFoundError("Material no encontrado en el catálogo.")
        if await self._suppliers.get("supplier", data.supplier_id) is None:
            raise NotFoundError("Proveedor no encontrado.")
        if data.quantity_g <= 0:
            raise ConflictError("La cantidad debe ser mayor que cero.")

        order = PurchaseOrder(
            tenant_id=self._tenant_id,
            order_code=generate_code("OC"),
            supplier_id=data.supplier_id,
            material_id=data.material_id,
            quantity_g=data.quantity_g,
            declared_purity=data.declared_purity,
            form=data.form,
            price_per_oz=data.price_per_oz,
            location=data.location,
            expected_delivery=data.expected_delivery,
            notes=data.notes,
        )
        await self._orders.add(order)
        created = await self._orders.get(order.id)
        assert created is not None
        return _to_view(created)

    async def approve_order(self, order_id: uuid.UUID) -> PurchaseOrderView:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de compra no encontrada.")
        if order.status != APPROVABLE_FROM:
            raise ConflictError(
                f"Sólo se puede aprobar una OC pendiente (estado actual: {order.status})."
            )

        lot = await self._inventory.register_lot(
            NewLot(
                material_id=order.material_id,
                form=order.form,  # type: ignore[arg-type]
                declared_purity=order.declared_purity,
                gross_weight_g=order.quantity_g,
                price_per_oz=order.price_per_oz,
                location=order.location,
                supplier_id=order.supplier_id,
                status="available",
            ),
            source_purchase_order_id=order.id,
        )
        order.status = "approved"
        order.lot_id = lot.id

        # Asiento automático: Dr Inventario / Cr Cuentas por Pagar (sección 7.12).
        amount = valuation_usd(order.quantity_g, order.declared_purity, order.price_per_oz)
        await self._accounting.record_purchase(
            PurchasePosting(
                supplier_id=order.supplier_id,
                supplier_name=order.supplier.legal_name if order.supplier else "—",
                amount=amount,
                source_id=order.id,
                source_code=order.order_code,
            )
        )
        return _to_view(order)

    async def reject_order(self, order_id: uuid.UUID) -> PurchaseOrderView:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de compra no encontrada.")
        if order.status != APPROVABLE_FROM:
            raise ConflictError(
                f"Sólo se puede rechazar una OC pendiente (estado actual: {order.status})."
            )
        order.status = "rejected"
        return _to_view(order)
