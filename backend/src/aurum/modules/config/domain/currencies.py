"""Dominio de Monedas configurables (sección 7.17).

Catálogo base sembrado por tenant. La moneda base se sincroniza con
``tenant_business_parameters.base_currency`` (sección 7.17): por defecto USD, pero
editable. Los importes se formatean según los decimales de cada moneda (COP usa 0).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrencyDef:
    code: str
    name: str
    symbol: str
    decimals: int


BASE_CURRENCIES: tuple[CurrencyDef, ...] = (
    CurrencyDef("USD", "Dólar estadounidense", "US$", 2),
    CurrencyDef("COP", "Peso colombiano", "$", 0),
    CurrencyDef("EUR", "Euro", "€", 2),
)
