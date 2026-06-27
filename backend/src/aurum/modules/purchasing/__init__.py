"""Módulo de Compras: órdenes de compra y flujo de aprobación (Fase 4, sección 7.2).

Una OC nace ``pending_approval``; al **aprobarse** (permiso ``purchase_order:approve``)
genera un lote de inventario con el material, peso, pureza y precio pactados
(criterio de aceptación de la Fase 4). Depende de Terceros (proveedor) e Inventario.
"""
