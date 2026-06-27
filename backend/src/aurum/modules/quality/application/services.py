"""Casos de uso de Calidad: registro de muestras y efecto sobre el lote (7.5).

Al registrar una muestra se copia la pureza declarada del lote y se calcula la
diferencia con la medida. Si el resultado es ``rejected`` el lote pasa a cuarentena
(lo que bloquea su avance en transformación); si es ``approved`` se levanta la
cuarentena previa, devolviéndolo a disponible.
"""

from __future__ import annotations

import uuid

from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.quality.application.dto import NewSample, QualityKpis, QualitySampleView
from aurum.modules.quality.application.ports import QualitySampleRepository
from aurum.modules.quality.infrastructure.models import QualitySample
from aurum.shared.codes import generate_code
from aurum.shared.errors import NotFoundError


def _to_view(sample: QualitySample) -> QualitySampleView:
    return QualitySampleView(
        id=sample.id,
        sample_code=sample.sample_code,
        lot_id=sample.lot_id,
        lot_code=sample.lot.lot_code if sample.lot else "—",
        material_name=sample.lot.material.name if sample.lot and sample.lot.material else "—",
        method=sample.method,  # type: ignore[arg-type]
        declared_purity=sample.declared_purity,
        measured_purity=sample.measured_purity,
        difference=sample.measured_purity - sample.declared_purity,
        analyst=sample.analyst,
        result=sample.result,  # type: ignore[arg-type]
        sampled_at=sample.sampled_at,
        created_at=sample.created_at,
    )


class QualityService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        samples: QualitySampleRepository,
        inventory: InventoryService,
    ) -> None:
        self._tenant_id = tenant_id
        self._samples = samples
        self._inventory = inventory

    async def list_samples(self) -> list[QualitySampleView]:
        return [_to_view(s) for s in await self._samples.list_all()]

    async def get_sample(self, sample_id: uuid.UUID) -> QualitySampleView:
        sample = await self._samples.get(sample_id)
        if sample is None:
            raise NotFoundError("Muestra no encontrada.")
        return _to_view(sample)

    async def kpis(self) -> QualityKpis:
        samples = await self._samples.list_all()
        return QualityKpis(
            total_samples=len(samples),
            approved=sum(1 for s in samples if s.result == "approved"),
            rejected=sum(1 for s in samples if s.result == "rejected"),
            pending=sum(1 for s in samples if s.result == "pending"),
        )

    async def create_sample(self, data: NewSample) -> QualitySampleView:
        lot = await self._inventory.get_lot(data.lot_id)  # valida existencia → 404

        sample = QualitySample(
            tenant_id=self._tenant_id,
            sample_code=generate_code("MUE"),
            lot_id=data.lot_id,
            method=data.method,
            declared_purity=lot.declared_purity,  # se copia del lote (fuente de verdad)
            measured_purity=data.measured_purity,
            analyst=data.analyst,
            result=data.result,
            sampled_at=data.sampled_at,
        )
        await self._samples.add(sample)

        # Efecto del veredicto sobre el lote (criterio de aceptación 7.5).
        if data.result == "rejected":
            await self._inventory.set_lot_status(data.lot_id, "quarantine")
        elif data.result == "approved" and lot.status == "quarantine":
            await self._inventory.set_lot_status(data.lot_id, "available")

        created = await self._samples.get(sample.id)
        assert created is not None
        return _to_view(created)
