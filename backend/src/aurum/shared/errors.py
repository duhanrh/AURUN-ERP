"""Excepciones de dominio y manejo global de errores.

Respuestas de error estandarizadas (sección 3.4):
``{ "status_code", "error", "message", "request_id" }``. Todo error 5xx se loggea
con su contexto (sección 3.9 / RNF-08).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from aurum.shared.request_context import get_request_id

logger = logging.getLogger("aurum.errors")


class DomainError(Exception):
    """Error de regla de negocio (mapeado a 4xx)."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"


def _payload(status_code: int, error: str, message: str) -> dict[str, object]:
    return {
        "status_code": status_code,
        "error": error,
        "message": message,
        "request_id": get_request_id(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de excepciones en la app."""

    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.status_code, exc.error_code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                **_payload(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "validation_error",
                    "La petición no superó la validación.",
                ),
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.status_code, "http_error", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # 100% de los 5xx loggeados con contexto (RNF-08).
        logger.exception("Error no controlado: %s", exc)
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            status_code=code,
            content=_payload(code, "internal_error", "Error interno del servidor."),
        )
