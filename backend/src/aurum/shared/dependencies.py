"""Dependencias transversales de FastAPI (sesión de BD y tenant requerido)."""

from __future__ import annotations

import uuid

from aurum.shared.errors import DomainError
from aurum.shared.infrastructure.database import get_session  # re-export
from aurum.shared.tenant_context import get_current_tenant_id

__all__ = ["get_session", "require_tenant_id"]


class TenantRequiredError(DomainError):
    status_code = 400
    error_code = "tenant_required"


def require_tenant_id() -> uuid.UUID:
    """Devuelve el tenant del contexto o falla si no se pudo resolver.

    El tenant lo fija el middleware (claim del JWT o cabecera de desarrollo). Su
    ausencia en una ruta que lo necesita es un error de cliente (falta token o
    cabecera), no un 500.
    """
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        raise TenantRequiredError("No se pudo resolver el tenant de la petición.")
    return tenant_id
