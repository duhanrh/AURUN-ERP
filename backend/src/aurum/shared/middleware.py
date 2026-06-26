"""Middleware transversal: request id y resolución de tenant.

**Resolución de tenant (sección 5.3).** El ``tenant_id`` se resuelve del lado del
servidor y es la frontera de RLS. Orden de prioridad:

1. **Claim firmado del access JWT** (``Authorization: Bearer``) — fuente de verdad
   para toda petición autenticada. Se verifica firma/``iss``/``aud``/``exp``.
2. Cabecera ``X-Tenant-ID`` — solo como apoyo en desarrollo y para el endpoint de
   login (que aún no tiene token). Nunca autoriza por sí sola.

Si el token es inválido o expirado, se ignora silenciosamente aquí: la dependencia
de autenticación de la ruta devolverá el 401 correspondiente.
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
        tenant_id = self._tenant_from_jwt(request) or self._tenant_from_header(request)
        set_current_tenant_id(tenant_id)
        request.state.tenant_id = tenant_id
        return await call_next(request)

    @staticmethod
    def _tenant_from_jwt(request: Request) -> uuid.UUID | None:
        """Tenant desde el claim firmado del access token, si lo hay y es válido."""
        auth = request.headers.get("Authorization", "")
        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        # Import diferido para evitar dependencia de auth en el arranque del módulo.
        import jwt as _jwt

        from aurum.modules.auth.infrastructure.security import TokenService

        try:
            return TokenService().decode_access_token(token).tenant_id
        except _jwt.InvalidTokenError:
            return None

    @staticmethod
    def _tenant_from_header(request: Request) -> uuid.UUID | None:
        raw = request.headers.get(TENANT_HEADER)
        if not raw:
            return None
        try:
            return uuid.UUID(raw)
        except ValueError:
            return None
