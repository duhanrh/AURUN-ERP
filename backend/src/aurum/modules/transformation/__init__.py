"""Módulo de Transformación: órdenes de proceso y pipeline de etapas (Fase 5, 7.4).

Una OT consume un lote de entrada y, al completarse, produce un lote de salida con
``peso_salida = peso_entrada × rendimiento``. El avance por el pipeline se bloquea
si el lote de entrada está en cuarentena por una muestra de laboratorio rechazada.
"""
