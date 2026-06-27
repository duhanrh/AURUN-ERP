"""Módulo de Inventario: catálogo de materiales y lotes (Fase 4, sección 7.1).

Núcleo de trazabilidad del material (O1): cada lote conoce su material, pureza,
peso bruto/disponible, ubicación y origen (proveedor). La valorización deriva de
``peso × pureza × precio`` (dominio ``valuation``). Compras alimenta el inventario
(OC aprobada → lote) y Ventas lo consume (OV → reduce stock disponible).
"""
