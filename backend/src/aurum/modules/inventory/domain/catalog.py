"""Catálogo base de materiales sembrado en cada tenant (sección 9 de la maqueta).

Metales preciosos con su símbolo de mercado (XAU/XAG/XPT/XPD) para futura conexión
a precios spot (Fase 7). Es la fuente de verdad del sembrado del provisionamiento;
cada tenant puede activar/desactivar materiales después, pero parte de este set.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaterialDef:
    code: str
    name: str
    symbol: str
    """Símbolo de cotización spot del metal (XAU, XAG, XPT, XPD)."""


BASE_MATERIALS: tuple[MaterialDef, ...] = (
    MaterialDef("AU24", "Oro 24K", "XAU"),
    MaterialDef("AU22", "Oro 22K", "XAU"),
    MaterialDef("AU18", "Oro 18K", "XAU"),
    MaterialDef("AG999", "Plata .999", "XAG"),
    MaterialDef("AG925", "Plata .925", "XAG"),
    MaterialDef("PT", "Platino", "XPT"),
    MaterialDef("PD", "Paladio", "XPD"),
)
