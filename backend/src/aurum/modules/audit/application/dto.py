"""DTOs del módulo de Auditoría."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditLogView:
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    changes: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditFilters:
    date_from: date | None = None
    date_to: date | None = None
    user_id: uuid.UUID | None = None
    entity_type: str | None = None
    action: str | None = None


@dataclass(frozen=True, slots=True)
class NewAuditEvent:
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    changes: dict[str, Any] | None = None
    user_id: uuid.UUID | None = None
    ip_address: str | None = None
