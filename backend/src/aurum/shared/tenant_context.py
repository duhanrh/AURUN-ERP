"""Contexto de tenant por petición (request-scoped).

El ``tenant_id`` se resuelve del lado del servidor (JWT/subdominio, sección 5.3) y
nunca se acepta del cliente como parámetro libre. Aquí se almacena en un
``ContextVar`` para que la capa de infraestructura lo aplique a la sesión de BD
(``SET LOCAL app.current_tenant_id``) sin que ningún repositorio tenga que pasarlo
explícitamente.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: uuid.UUID | None) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id() -> uuid.UUID | None:
    return _current_tenant_id.get()
