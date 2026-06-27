"""Protección anti fuerza bruta del login (sección 10.x / RNF de seguridad).

Bloqueo temporal tras N intentos fallidos consecutivos por (tenant, email), con
ventana deslizante en memoria. En un despliegue multi-instancia los contadores
deben respaldarse en Redis; esta versión en proceso mantiene la decisión idéntica
(permitido / bloqueado) para una sola instancia.
"""

from __future__ import annotations

import time

_MAX_FAILURES = 5
_WINDOW_SECONDS = 300  # 5 minutos

# key -> lista de timestamps (monotónicos) de fallos recientes
_failures: dict[str, list[float]] = {}


def _prune(key: str, now: float) -> list[float]:
    recent = [t for t in _failures.get(key, []) if now - t < _WINDOW_SECONDS]
    if recent:
        _failures[key] = recent
    else:
        _failures.pop(key, None)
    return recent


def is_blocked(key: str) -> bool:
    """``True`` si la clave acumuló demasiados fallos dentro de la ventana."""
    return len(_prune(key, time.monotonic())) >= _MAX_FAILURES


def record_failure(key: str) -> None:
    now = time.monotonic()
    recent = _prune(key, now)
    recent.append(now)
    _failures[key] = recent


def reset(key: str) -> None:
    """Limpia los fallos de una clave (login exitoso)."""
    _failures.pop(key, None)


def clear_all() -> None:
    """Limpia todo (uso en pruebas)."""
    _failures.clear()
