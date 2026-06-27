"""DTOs del módulo de Terceros (independientes del ORM y de la API)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from aurum.modules.terceros.domain.party import PartyKind, PartyStatus


@dataclass(frozen=True, slots=True)
class PartyView:
    """Vista de lectura de un tercero (cliente o proveedor)."""

    id: uuid.UUID
    kind: PartyKind
    legal_name: str
    tax_id: str
    status: PartyStatus
    country: str | None = None
    city: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    # Proveedor
    main_material: str | None = None
    certifications: str | None = None
    rating: float | None = None
    # Cliente
    segment: str | None = None
    preferred_material: str | None = None
    credit_limit: float | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PartyKpis:
    """KPIs de cabecera del listado (sección 7.5/7.6: total y desglose por estado)."""

    total: int
    active: int
    evaluation: int
    inactive: int


@dataclass(frozen=True, slots=True)
class NewParty:
    """Datos de alta de un tercero (modal Nuevo Cliente/Proveedor)."""

    legal_name: str
    tax_id: str
    status: PartyStatus = "active"
    country: str | None = None
    city: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    main_material: str | None = None
    certifications: str | None = None
    rating: float | None = None
    segment: str | None = None
    preferred_material: str | None = None
    credit_limit: float | None = None


@dataclass(frozen=True, slots=True)
class PartyPatch:
    """Cambios parciales de un tercero; ``None`` = no tocar ese campo.

    ``_SENTINEL`` distingue "no enviado" de "enviado como null"; la presentación
    sólo rellena los campos presentes en el cuerpo de la petición.
    """

    legal_name: str | None = None
    tax_id: str | None = None
    status: PartyStatus | None = None
    country: str | None = None
    city: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    main_material: str | None = None
    certifications: str | None = None
    rating: float | None = None
    segment: str | None = None
    preferred_material: str | None = None
    credit_limit: float | None = None
    fields_set: frozenset[str] = frozenset()
