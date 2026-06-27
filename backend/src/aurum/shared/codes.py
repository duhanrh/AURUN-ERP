"""Generación de códigos legibles para documentos de negocio (OC, OV, lotes).

Formato ``<PREFIJO>-<8 hex>`` (p. ej. ``OC-1A2B3C4D``): único por la entropía del
UUID y suficientemente corto para mostrarse en tablas. La unicidad fuerte la
garantiza igualmente el índice ``(tenant_id, code)`` de cada tabla.
"""

from __future__ import annotations

import uuid


def generate_code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
