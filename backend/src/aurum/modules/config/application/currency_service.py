"""Casos de uso de Monedas configurables (sección 7.17).

CRUD con borrado lógico. Una sola moneda es la **base** del tenant; al fijarla, se
sincroniza ``tenant_business_parameters.base_currency`` para que exista una única
fuente de verdad (la tabla de monedas) sin romper a quien lee el parámetro legado.
La moneda base no se puede eliminar ni desactivar.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aurum.modules.config.application.dto import CurrencyCreate, CurrencyPatch, CurrencyView
from aurum.modules.config.application.ports import CurrencyRepository, ParametersRepository
from aurum.modules.config.infrastructure.models import Currency
from aurum.shared.errors import ConflictError, NotFoundError


def _to_view(c: Currency) -> CurrencyView:
    return CurrencyView(
        id=str(c.id),
        code=c.code,
        name=c.name,
        symbol=c.symbol,
        decimals=c.decimals,
        is_base=c.is_base,
        is_active=c.is_active,
        is_deleted=c.deleted_at is not None,
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class CurrencyService:
    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        currencies: CurrencyRepository,
        parameters: ParametersRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._currencies = currencies
        self._parameters = parameters

    async def list_currencies(self, *, include_deleted: bool = False) -> list[CurrencyView]:
        rows = await self._currencies.list_all(include_deleted=include_deleted)
        return [_to_view(c) for c in rows]

    async def create_currency(self, data: CurrencyCreate) -> CurrencyView:
        code = data.code.strip().upper()
        if not code:
            raise ConflictError("El código de la moneda es obligatorio.")
        if await self._currencies.get_by_code(code) is not None:
            raise ConflictError(f"Ya existe una moneda con el código '{code}'.")
        currency = Currency(
            tenant_id=self._tenant_id,
            code=code,
            name=data.name.strip(),
            symbol=data.symbol.strip(),
            decimals=data.decimals,
            is_base=False,
            is_active=data.is_active,
        )
        return _to_view(await self._currencies.add(currency))

    async def update_currency(self, currency_id: uuid.UUID, patch: CurrencyPatch) -> CurrencyView:
        currency = await self._require(currency_id)
        if patch.name is not None:
            currency.name = patch.name.strip()
        if patch.symbol is not None:
            currency.symbol = patch.symbol.strip()
        if patch.decimals is not None:
            currency.decimals = patch.decimals
        if patch.is_active is not None:
            if currency.is_base and not patch.is_active:
                raise ConflictError("La moneda base no se puede desactivar.")
            currency.is_active = patch.is_active
        return _to_view(currency)

    async def set_base(self, currency_id: uuid.UUID) -> CurrencyView:
        target = await self._require(currency_id)
        if target.deleted_at is not None:
            raise ConflictError("No se puede fijar como base una moneda eliminada.")
        for currency in await self._currencies.list_all():
            currency.is_base = currency.id == target.id
        target.is_active = True
        params = await self._parameters.get()
        if params is not None:  # mantener el parámetro legado en sincronía
            params.base_currency = target.code
        return _to_view(target)

    async def delete_currency(self, currency_id: uuid.UUID) -> CurrencyView:
        currency = await self._require(currency_id)
        if currency.is_base:
            raise ConflictError("La moneda base no se puede eliminar.")
        currency.deleted_at = _now()
        return _to_view(currency)

    async def restore_currency(self, currency_id: uuid.UUID) -> CurrencyView:
        currency = await self._require(currency_id)
        if currency.deleted_at is None:
            raise ConflictError("La moneda no está eliminada.")
        clash = await self._currencies.get_by_code(currency.code)
        if clash is not None and clash.id != currency.id:
            raise ConflictError(f"Ya existe una moneda vigente con el código '{currency.code}'.")
        currency.deleted_at = None
        return _to_view(currency)

    async def _require(self, currency_id: uuid.UUID) -> Currency:
        currency = await self._currencies.get(currency_id)
        if currency is None:
            raise NotFoundError("Moneda no encontrada.")
        return currency
