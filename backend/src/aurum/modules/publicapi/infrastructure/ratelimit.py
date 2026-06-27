"""Rate limiting en memoria para la API pública (sección 10.9).

Ventana fija por API Key, más estricta que el límite interno. En un despliegue
multi-instancia, los contadores deben respaldarse en Redis (sección 10.9); esta
implementación en proceso es suficiente para una sola instancia y mantiene la
forma de la decisión (permitido / 429) idéntica.
"""

from __future__ import annotations

import time

_WINDOW_SECONDS = 60
_MAX_REQUESTS = 60

# prefix -> (window_start_epoch, count)
_buckets: dict[str, tuple[float, int]] = {}


def check_rate_limit(identifier: str, *, limit: int = _MAX_REQUESTS) -> bool:
    """Devuelve ``True`` si la petición está permitida; ``False`` si excede el límite."""
    now = time.monotonic()
    window_start, count = _buckets.get(identifier, (now, 0))
    if now - window_start >= _WINDOW_SECONDS:
        _buckets[identifier] = (now, 1)
        return True
    if count >= limit:
        return False
    _buckets[identifier] = (window_start, count + 1)
    return True


def reset() -> None:
    """Limpia los contadores (uso en pruebas)."""
    _buckets.clear()
