"""Casos de uso del Inventario: materiales, lotes, KPIs y registro de stock.

``register_lot`` es el punto de entrada que también usa Compras al aprobar una OC
(el lote nace de la compra). ``consume_lot`` lo usa Ventas para descontar stock con
la invariante de no vender por encima de lo disponible (sección 7.3).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from aurum.modules.inventory.application.dto import (
    InventoryKpis,
    LotPatch,
    LotView,
    MaterialPatch,
    MaterialView,
    NewLot,
    NewMaterial,
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
    return MaterialView(
        id=m.id,
        code=m.code,
        name=m.name,
        symbol=m.symbol,
        is_active=m.is_active,
        is_deleted=m.deleted_at is not None,
    )


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
        is_deleted=lot.deleted_at is not None,
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

    async def list_catalog(self, *, include_deleted: bool = False) -> list[MaterialView]:
        materials = await self._materials.list_catalog(include_deleted=include_deleted)
        return [_material_to_view(m) for m in materials]

    async def create_material(self, data: NewMaterial) -> MaterialView:
        code = data.code.strip().upper()
        if not code:
            raise ConflictError("El código del material es obligatorio.")
        if await self._materials.exists_code(code):
            raise ConflictError(f"Ya existe un material con el código '{code}'.")
        material = Material(
            tenant_id=self._tenant_id,
            code=code,
            name=data.name.strip(),
            symbol=data.symbol.strip(),
            is_active=data.is_active,
        )
        await self._materials.add(material)
        return _material_to_view(material)

    async def update_material(self, material_id: uuid.UUID, patch: MaterialPatch) -> MaterialView:
        material = await self._materials.get(material_id)
        if material is None:
            raise NotFoundError("Material no encontrado.")
        if "name" in patch.fields_set and patch.name is not None:
            material.name = patch.name.strip()
        if "symbol" in patch.fields_set and patch.symbol is not None:
            material.symbol = patch.symbol.strip()
        if "is_active" in patch.fields_set and patch.is_active is not None:
            material.is_active = patch.is_active
        return _material_to_view(material)

    async def delete_material(self, material_id: uuid.UUID) -> MaterialView:
        material = await self._materials.get(material_id)
        if material is None:
            raise NotFoundError("Material no encontrado.")
        material.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return _material_to_view(material)

    async def restore_material(self, material_id: uuid.UUID) -> MaterialView:
        material = await self._materials.get(material_id, include_deleted=True)
        if material is None:
            raise NotFoundError("Material no encontrado.")
        if material.deleted_at is None:
            raise ConflictError("El material no está eliminado.")
        if await self._materials.exists_code(material.code, exclude_id=material.id):
            raise ConflictError(
                "No se puede restaurar: ya existe un material vigente con ese código."
            )
        material.deleted_at = None
        return _material_to_view(material)

    async def list_lots(self, *, include_deleted: bool = False) -> list[LotView]:
        lots = await self._lots.list_all(include_deleted=include_deleted)
        return [_lot_to_view(lot) for lot in lots]

    async def get_lot(self, lot_id: uuid.UUID) -> LotView:
        lot = await self._lots.get(lot_id)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        return _lot_to_view(lot)

    async def update_lot(self, lot_id: uuid.UUID, patch: LotPatch) -> LotView:
        lot = await self._lots.get(lot_id)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        if "location" in patch.fields_set:
            lot.location = patch.location
        if "status" in patch.fields_set and patch.status is not None:
            lot.status = patch.status
        return _lot_to_view(lot)

    async def delete_lot(self, lot_id: uuid.UUID) -> LotView:
        """Baja lógica de un lote, sólo si no ha tenido movimientos de stock."""
        lot = await self._lots.get(lot_id)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        if lot.available_weight_g != lot.gross_weight_g:
            raise ConflictError(
                "No se puede eliminar un lote con movimientos de stock (consumido o vendido)."
            )
        lot.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return _lot_to_view(lot)

    async def undelete_lot(self, lot_id: uuid.UUID) -> LotView:
        lot = await self._lots.get(lot_id, include_deleted=True)
        if lot is None:
            raise NotFoundError("Lote no encontrado.")
        if lot.deleted_at is None:
            raise ConflictError("El lote no está eliminado.")
        lot.deleted_at = None
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

    async def is_lot_blocked(self, lot_id: uuid.UUID) -> bool:
        """Un lote en cuarentena (muestra de lab rechazada) está bloqueado (7.5)."""
        lot = await self._lots.get(lot_id)
        return lot is not None and lot.status == "quarantine"

    async def set_lot_status(self, lot_id: uuid.UUID, status: str) -> InventoryLot | None:
        """Cambia el estado de un lote (p. ej. ``quarantine`` desde Calidad)."""
        lot = await self._lots.get(lot_id)
        if lot is None:
            return None
        lot.status = status
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
