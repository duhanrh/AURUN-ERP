"""Casos de uso del Inventario: materiales, lotes, KPIs y registro de stock.

``register_lot`` es el punto de entrada que también usa Compras al aprobar una OC
(el lote nace de la compra). ``consume_lot`` lo usa Ventas para descontar stock con
la invariante de no vender por encima de lo disponible (sección 7.3).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from aurum.modules.inventory.application.dto import (
    InventoryKpis,
    LotView,
    MaterialView,
    NewLot,
)
from aurum.modules.inventory.application.ports import LotRepository, MaterialRepository
from aurum.modules.inventory.domain.valuation import (
    DEFAULT_LOT_STATUS,
    fine_weight_g,
    valuation_usd,
)
from aurum.modules.inventory.infrastructure.models import InventoryLot, Material
from aurum.shared.codes import generate_code
from aurum.shared.errors import ConflictError, DomainError, NotFoundError


class InsufficientStockError(DomainError):
    status_code = 409
    error_code = "insufficient_stock"


def _material_to_view(m: Material) -> MaterialView:
    return MaterialView(id=m.id, code=m.code, name=m.name, symbol=m.symbol, is_active=m.is_active)


def _lot_to_view(lot: InventoryLot) -> LotView:
    return LotView(
        id=lot.id,
        lot_code=lot.lot_code,
        material_id=lot.material_id,
        material_code=lot.material.code,
        material_name=lot.material.name,
        form=lot.form,  # type: ignore[arg-type]
        declared_purity=lot.declared_purity,
        gross_weight_g=lot.gross_weight_g,
        available_weight_g=lot.available_weight_g,
        net_weight_g=fine_weight_g(lot.available_weight_g, lot.declared_purity),
        price_per_oz=lot.price_per_oz,
        value_usd=valuation_usd(lot.available_weight_g, lot.declared_purity, lot.price_per_oz),
        status=lot.status,  # type: ignore[arg-type]
        location=lot.location,
        supplier_id=lot.supplier_id,
        entry_date=lot.entry_date,
        created_at=lot.created_at,
    )


class InventoryService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        lots: LotRepository,
        materials: MaterialRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._lots = lots
        self._materials = materials

    async def list_materials(self) -> list[MaterialView]:
        return [_material_to_view(m) for m in await self._materials.list_active()]

    async def list_lots(self) -> list[LotView]:
        return [_lot_to_view(lot) for lot in await self._lots.list_all()]

    async def get_lot(self, lot_id: uuid.UUID) -> LotView:
        lot = await self._lots.get(lot_id)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        return _lot_to_view(lot)

    async def kpis(self) -> InventoryKpis:
        lots = await self._lots.list_all()
        total_value = sum(
            (
                valuation_usd(lot.available_weight_g, lot.declared_purity, lot.price_per_oz)
                for lot in lots
            ),
            Decimal("0"),
        )
        total_weight = sum((lot.available_weight_g for lot in lots), Decimal("0"))
        raw = sum(1 for lot in lots if lot.form == "raw")
        return InventoryKpis(
            total_lots=len(lots),
            total_gross_weight_g=total_weight,
            total_value_usd=total_value,
            raw_lots=raw,
            refined_lots=len(lots) - raw,
        )

    async def create_lot(self, data: NewLot) -> LotView:
        material = await self._materials.get(data.material_id)
        if material is None:
            raise NotFoundError("Material no encontrado en el catálogo.")
        lot = await self.register_lot(data)
        return _lot_to_view(lot)

    async def register_lot(
        self, data: NewLot, *, source_purchase_order_id: uuid.UUID | None = None
    ) -> InventoryLot:
        """Crea y persiste un lote (uso interno y desde Compras al aprobar)."""
        if data.gross_weight_g <= 0:
            raise ConflictError("El peso bruto debe ser mayor que cero.")
        code = data.lot_code or generate_code("LOT")
        if await self._lots.exists_code(code):
            raise ConflictError(f"Ya existe un lote con el código '{code}'.")
        lot = InventoryLot(
            tenant_id=self._tenant_id,
            lot_code=code,
            material_id=data.material_id,
            form=data.form,
            declared_purity=data.declared_purity,
            gross_weight_g=data.gross_weight_g,
            available_weight_g=data.gross_weight_g,
            price_per_oz=data.price_per_oz,
            location=data.location,
            status=data.status or DEFAULT_LOT_STATUS,
            entry_date=data.entry_date,
            supplier_id=data.supplier_id,
            source_purchase_order_id=source_purchase_order_id,
        )
        return await self._lots.add(lot)

    async def consume_lot(self, lot_id: uuid.UUID, quantity_g: Decimal) -> InventoryLot:
        """Descuenta ``quantity_g`` del stock disponible de un lote (venta)."""
        lot = await self._lots.get(lot_id)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        if quantity_g <= 0:
            raise ConflictError("La cantidad a vender debe ser mayor que cero.")
        if quantity_g > lot.available_weight_g:
            raise InsufficientStockError(
                f"Stock insuficiente: disponible {lot.available_weight_g} g, "
                f"solicitado {quantity_g} g."
            )
        lot.available_weight_g = lot.available_weight_g - quantity_g
        if lot.available_weight_g == 0:
            lot.status = "reserved"
        return lot

    async def restore_lot(self, lot_id: uuid.UUID, quantity_g: Decimal) -> InventoryLot | None:
        """Devuelve ``quantity_g`` al stock de un lote (cancelación de venta)."""
        lot = await self._lots.get(lot_id)
        if lot is None:
            return None
        lot.available_weight_g = lot.available_weight_g + quantity_g
        if lot.status == "reserved" and lot.available_weight_g > 0:
            lot.status = "available"
        return lot
