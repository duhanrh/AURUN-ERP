"""Casos de uso de Unidades de Medida configurables (sección 7.17).

CRUD con borrado lógico (``deleted_at``), conservando el patrón del resto de
maestros. La unidad base (``is_base``) no se puede eliminar ni desactivar, porque
es el ancla de todas las conversiones (factor 1 = gramo).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from aurum.modules.config.application.dto import UnitCreate, UnitPatch, UnitView
from aurum.modules.config.application.ports import UnitOfMeasureRepository
from aurum.modules.config.domain.units import grams_to_unit, unit_to_grams
from aurum.modules.config.infrastructure.models import UnitOfMeasure
from aurum.shared.errors import ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class ConversionResult:
    grams: Decimal
    result: Decimal


def _to_view(u: UnitOfMeasure) -> UnitView:
    return UnitView(
        id=str(u.id),
        code=u.code,
        name=u.name,
        symbol=u.symbol,
        grams_factor=u.grams_factor,
        is_base=u.is_base,
        is_active=u.is_active,
        is_deleted=u.deleted_at is not None,
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class UnitOfMeasureService:
    def __init__(self, *, tenant_id: uuid.UUID, units: UnitOfMeasureRepository) -> None:
        self._tenant_id = tenant_id
        self._units = units

    async def list_units(self, *, include_deleted: bool = False) -> list[UnitView]:
        rows = await self._units.list_all(include_deleted=include_deleted)
        return [_to_view(u) for u in rows]

    async def create_unit(self, data: UnitCreate) -> UnitView:
        code = data.code.strip().lower()
        if not code:
            raise ConflictError("El código de la unidad es obligatorio.")
        if data.grams_factor <= Decimal("0"):
            raise ConflictError("El factor a gramos debe ser mayor que cero.")
        if await self._units.get_by_code(code) is not None:
            raise ConflictError(f"Ya existe una unidad con el código '{code}'.")
        unit = UnitOfMeasure(
            tenant_id=self._tenant_id,
            code=code,
            name=data.name.strip(),
            symbol=data.symbol.strip(),
            grams_factor=data.grams_factor,
            is_base=False,
            is_active=data.is_active,
        )
        return _to_view(await self._units.add(unit))

    async def update_unit(self, unit_id: uuid.UUID, patch: UnitPatch) -> UnitView:
        unit = await self._require(unit_id)
        if patch.grams_factor is not None:
            if unit.is_base:
                raise ConflictError("No se puede cambiar el factor de la unidad base.")
            if patch.grams_factor <= Decimal("0"):
                raise ConflictError("El factor a gramos debe ser mayor que cero.")
            unit.grams_factor = patch.grams_factor
        if patch.name is not None:
            unit.name = patch.name.strip()
        if patch.symbol is not None:
            unit.symbol = patch.symbol.strip()
        if patch.is_active is not None:
            if unit.is_base and not patch.is_active:
                raise ConflictError("La unidad base no se puede desactivar.")
            unit.is_active = patch.is_active
        return _to_view(unit)

    async def delete_unit(self, unit_id: uuid.UUID) -> UnitView:
        unit = await self._require(unit_id)
        if unit.is_base:
            raise ConflictError("La unidad base (gramo) no se puede eliminar.")
        unit.deleted_at = _now()
        return _to_view(unit)

    async def restore_unit(self, unit_id: uuid.UUID) -> UnitView:
        unit = await self._require(unit_id)
        if unit.deleted_at is None:
            raise ConflictError("La unidad no está eliminada.")
        clash = await self._units.get_by_code(unit.code)
        if clash is not None and clash.id != unit.id:
            raise ConflictError(f"Ya existe una unidad vigente con el código '{unit.code}'.")
        unit.deleted_at = None
        return _to_view(unit)

    async def convert(self, quantity: Decimal, from_code: str, to_code: str) -> ConversionResult:
        """Convierte ``quantity`` de la unidad ``from_code`` a ``to_code`` vía gramos."""
        source = await self._require_code(from_code)
        target = await self._require_code(to_code)
        grams = unit_to_grams(quantity, source.grams_factor)
        result = grams_to_unit(grams, target.grams_factor)
        return ConversionResult(grams=grams, result=result)

    async def _require(self, unit_id: uuid.UUID) -> UnitOfMeasure:
        unit = await self._units.get(unit_id)
        if unit is None:
            raise NotFoundError("Unidad de medida no encontrada.")
        return unit

    async def _require_code(self, code: str) -> UnitOfMeasure:
        unit = await self._units.get_by_code(code.strip().lower())
        if unit is None:
            raise NotFoundError(f"Unidad de medida '{code}' no encontrada.")
        return unit
