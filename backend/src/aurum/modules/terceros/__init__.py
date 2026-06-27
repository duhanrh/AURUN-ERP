"""Módulo de Terceros: Clientes y Proveedores (Fase 3, secciones 7.5/7.6).

Modela el maestro de terceros del tenant con una única entidad ``Party``
discriminada por ``kind`` (``customer`` / ``supplier``). Comparte identidad y
contacto; cada tipo añade sus atributos propios (segmento/línea de crédito para
clientes; material principal/certificaciones/rating para proveedores).
"""
