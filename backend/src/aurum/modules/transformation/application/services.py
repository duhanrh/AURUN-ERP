"""Casos de uso de Transformación: pipeline, avance y cierre con yield (7.4).

Reglas (criterios de aceptación de la Fase 5):
- Avanzar/completar una OT se **bloquea** si el lote de entrada está en cuarentena
  (muestra de laboratorio rechazada).
- Al **completarse**, consume el peso de entrada del lote origen y crea el lote de
  salida con ``peso_entrada × rendimiento`` (vinculación entrada → salida).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aurum.modules.inventory.application.dto import NewLot
from aurum.modules.inventory.application.ports import MaterialRepository
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.transformation.application.dto import (
    NewTransformationOrder,
    TransformationKpis,
    TransformationOrderPatch,
    TransformationOrderView,
)
from aurum.modules.transformation.application.ports import TransformationOrderRepository
from aurum.modules.transformation.domain.pipeline import (
    FIRST_STAGE,
    LAST_STAGE,
    next_stage,
    output_weight_g,
)
from aurum.modules.transformation.infrastructure.models import TransformationOrder
from aurum.shared.codes import generate_code
from aurum.shared.errors import ConflictError, DomainError, NotFoundError


class PipelineBlockedError(DomainError):
    status_code = 409
    error_code = "pipeline_blocked"


def _to_view(order: TransformationOrder) -> TransformationOrderView:
    blocked = order.input_lot is not None and order.input_lot.status == "quarantine"
    return TransformationOrderView(
        id=order.id,
        order_code=order.order_code,
        input_lot_id=order.input_lot_id,
        input_lot_code=order.input_lot.lot_code if order.input_lot else "—",
        input_material_name=(
            order.input_lot.material.name if order.input_lot and order.input_lot.material else "—"
        ),
        process=order.process,  # type: ignore[arg-type]
        input_quantity_g=order.input_quantity_g,
        yield_fraction=order.yield_fraction,
        output_material_id=order.output_material_id,
        output_material_name=order.output_material.name if order.output_material else "—",
        output_form=order.output_form,  # type: ignore[arg-type]
        output_purity=order.output_purity,
        expected_output_g=output_weight_g(order.input_quantity_g, order.yield_fraction),
        stage=order.stage,  # type: ignore[arg-type]
        status=order.status,  # type: ignore[arg-type]
        blocked=blocked,
        responsible=order.responsible,
        started_at=order.started_at,
        expected_end=order.expected_end,
        output_lot_id=order.output_lot_id,
        created_at=order.created_at,
        is_deleted=order.deleted_at is not None,
    )


class TransformationService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        orders: TransformationOrderRepository,
        inventory: InventoryService,
        materials: MaterialRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._orders = orders
        self._inventory = inventory
        self._materials = materials

    async def list_orders(self, *, include_deleted: bool = False) -> list[TransformationOrderView]:
        orders = await self._orders.list_all(include_deleted=include_deleted)
        return [_to_view(o) for o in orders]

    async def get_order(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._require(order_id)
        return _to_view(order)

    async def kpis(self) -> TransformationKpis:
        orders = await self._orders.list_all()
        blocked = sum(
            1
            for o in orders
            if o.status == "in_progress"
            and o.input_lot is not None
            and o.input_lot.status == "quarantine"
        )
        return TransformationKpis(
            total_orders=len(orders),
            in_progress=sum(1 for o in orders if o.status == "in_progress"),
            completed=sum(1 for o in orders if o.status == "completed"),
            blocked=blocked,
        )

    async def create_order(self, data: NewTransformationOrder) -> TransformationOrderView:
        input_lot = await self._inventory.get_lot(data.input_lot_id)  # valida existencia → 404
        if await self._materials.get(data.output_material_id) is None:
            raise NotFoundError("Material de salida no encontrado.")
        if data.input_quantity_g > input_lot.available_weight_g:
            raise ConflictError(
                "La cantidad a transformar excede el stock disponible del lote de entrada."
            )

        order = TransformationOrder(
            tenant_id=self._tenant_id,
            order_code=generate_code("OT"),
            input_lot_id=data.input_lot_id,
            process=data.process,
            input_quantity_g=data.input_quantity_g,
            yield_fraction=data.yield_fraction,
            output_material_id=data.output_material_id,
            output_form=data.output_form,
            output_purity=data.output_purity,
            stage=FIRST_STAGE,
            status="in_progress",
            responsible=data.responsible,
            started_at=data.started_at,
            expected_end=data.expected_end,
        )
        await self._orders.add(order)
        created = await self._require(order.id)
        return _to_view(created)

    async def advance_stage(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._require(order_id)
        if order.status != "in_progress":
            raise ConflictError(f"La OT no está en curso (estado: {order.status}).")
        await self._guard_not_blocked(order)
        upcoming = next_stage(order.stage)  # type: ignore[arg-type]
        if upcoming is None:
            raise ConflictError("La OT ya está en la última etapa; complétala para cerrarla.")
        order.stage = upcoming
        return _to_view(order)

    async def complete_order(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._require(order_id)
        if order.status != "in_progress":
            raise ConflictError(f"La OT no está en curso (estado: {order.status}).")
        await self._guard_not_blocked(order)

        # Consume el lote de entrada (valida stock) y crea el de salida.
        await self._inventory.consume_lot(order.input_lot_id, order.input_quantity_g)
        produced = output_weight_g(order.input_quantity_g, order.yield_fraction)
        output_lot = await self._inventory.register_lot(
            NewLot(
                material_id=order.output_material_id,
                form=order.output_form,  # type: ignore[arg-type]
                declared_purity=order.output_purity,
                gross_weight_g=produced,
                # El lote de salida hereda el costo/oz del de entrada (base de costo).
                price_per_oz=order.input_lot.price_per_oz,
                location=order.input_lot.location,
                status="available",
            )
        )
        order.output_lot_id = output_lot.id
        order.stage = LAST_STAGE
        order.status = "completed"
        return _to_view(order)

    async def cancel_order(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._require(order_id)
        if order.status != "in_progress":
            raise ConflictError(f"La OT no está en curso (estado: {order.status}).")
        order.status = "cancelled"
        return _to_view(order)

    async def update_order(
        self, order_id: uuid.UUID, patch: TransformationOrderPatch
    ) -> TransformationOrderView:
        order = await self._require(order_id)
        if order.status != "in_progress":
            raise ConflictError(f"Sólo se puede editar una OT en curso (estado: {order.status}).")
        for attr in ("responsible", "started_at", "expected_end"):
            if attr in patch.fields_set:
                setattr(order, attr, getattr(patch, attr))
        return _to_view(order)

    async def delete_order(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._require(order_id)
        if order.status == "in_progress":
            raise ConflictError("Cancela la OT en curso antes de eliminarla.")
        order.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        return _to_view(order)

    async def restore_order(self, order_id: uuid.UUID) -> TransformationOrderView:
        order = await self._orders.get(order_id, include_deleted=True)
        if order is None:
            raise NotFoundError("Orden de transformación no encontrada.")
        if order.deleted_at is None:
            raise ConflictError("La OT no está eliminada.")
        order.deleted_at = None
        return _to_view(order)

    async def _require(self, order_id: uuid.UUID) -> TransformationOrder:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Orden de transformación no encontrada.")
        return order

    async def _guard_not_blocked(self, order: TransformationOrder) -> None:
        if await self._inventory.is_lot_blocked(order.input_lot_id):
            raise PipelineBlockedError(
                "El lote de entrada está en cuarentena por una muestra rechazada; "
                "no puede avanzar en el pipeline."
            )
