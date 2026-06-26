"""Logging estructurado en JSON (sección 3.9).

Cada línea de log incluye ``request_id`` y ``tenant_id`` cuando están disponibles
en el contexto de la petición. Sin dependencias externas (stdlib ``logging``).
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from aurum.shared.request_context import get_request_id
from aurum.shared.tenant_context import get_current_tenant_id


class JsonFormatter(logging.Formatter):
    """Formatea los registros como JSON con contexto de tenant/petición."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id

        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            payload["tenant_id"] = str(tenant_id)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configura el logging raíz con salida JSON a stdout (idempotente)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
