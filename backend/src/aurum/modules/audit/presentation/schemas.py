"""Esquemas Pydantic de la API de Auditoría (sección 7.18)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from aurum.modules.audit.application.dto import AuditLogView


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    changes: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime

    @classmethod
    def from_view(cls, v: AuditLogView) -> AuditLogResponse:
        return cls(
            id=v.id,
            user_id=v.user_id,
            action=v.action,
            entity_type=v.entity_type,
            entity_id=v.entity_id,
            changes=v.changes,
            ip_address=v.ip_address,
            created_at=v.created_at,
        )
