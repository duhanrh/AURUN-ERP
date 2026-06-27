"""Dominio de Configuración: catálogo de módulos y parámetros por defecto (7.17).

- ``TOGGLEABLE_MODULES``: módulos que un tenant puede activar/desactivar (los del
  menú de negocio). Dashboard y Configuración son núcleo y no se listan aquí.
- ``DEFAULT_PARAMETERS``: valores de negocio por defecto sembrados en cada tenant
  (moneda, unidad de peso, stock mínimo, margen mínimo, idioma, zona horaria…),
  todos ya presentes como campos en la maqueta (`page-configuracion` → Parámetros).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ModuleDef:
    key: str
    label: str


# Módulos de negocio activables por tenant (claves alineadas con la navegación).
TOGGLEABLE_MODULES: tuple[ModuleDef, ...] = (
    ModuleDef("inventario", "Inventario"),
    ModuleDef("compras", "Compras"),
    ModuleDef("ventas", "Ventas"),
    ModuleDef("transformacion", "Transformación"),
    ModuleDef("proveedores", "Proveedores"),
    ModuleDef("clientes", "Clientes"),
    ModuleDef("calidad", "Calidad / Laboratorio"),
    ModuleDef("finanzas", "Contabilidad"),
    ModuleDef("reportes", "Reportes"),
)

MODULE_KEYS: frozenset[str] = frozenset(m.key for m in TOGGLEABLE_MODULES)


@dataclass(frozen=True, slots=True)
class BusinessParametersDefaults:
    base_currency: str = "USD"
    weight_unit: str = "g"
    min_stock_g: Decimal = Decimal("1000")
    min_margin_pct: Decimal = Decimal("5")
    language: str = "es"
    timezone: str = "America/Bogota"
    date_format: str = "YYYY-MM-DD"
    regulatory_entity: str = ""


DEFAULT_PARAMETERS = BusinessParametersDefaults()

WEIGHT_UNITS = ("g", "kg", "oz")
CURRENCIES = ("USD", "COP", "EUR")
