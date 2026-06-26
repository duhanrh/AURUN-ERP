"""Middleware transversal: request id y resolución de tenant.

**Resolución de tenant (Fase 1 — esqueleto).** El ``tenant_id`` debe resolverse
del lado del servidor (sección 5.3). En Fase 2 vendrá del claim firmado del JWT;
por ahora, en desarrollo, se acepta la cabecera ``X-Tenant-ID`` para poder probar
RLS. Nunca se confía en el cliente para autorizar (eso llega con Auth en Fase 2).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aurum.shared.request_context import set_request_id
from aurum.shared.tenant_context import set_current_tenant_id

RequestHandler = Callable[[Request], Awaitable[Response]]

REQUEST_ID_HEADER = "X-Request-ID"
TENANT_HEADER = "X-Tenant-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Asigna un ``request_id`` a cada petición y lo devuelve en la respuesta."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        set_request_id(request_id)
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class TenantResolutionMiddleware(BaseHTTPMiddleware):
    """Resuelve el tenant de la petición y lo deja en el contexto (request-scoped)."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        tenant_id: uuid.UUID | None = None
        raw = request.headers.get(TENANT_HEADER)
        if raw:
            try:
                tenant_id = uuid.UUID(raw)
            except ValueError:
                tenant_id = None

        set_current_tenant_id(tenant_id)
        request.state.tenant_id = tenant_id
        return await call_next(request)
