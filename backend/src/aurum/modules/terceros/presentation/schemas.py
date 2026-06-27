"""Esquemas Pydantic de la API de Terceros (Clientes/Proveedores, secciones 7.5/7.6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from aurum.modules.terceros.application.dto import (
    NewParty,
    PartyKpis,
    PartyPatch,
    PartyView,
)
from aurum.modules.terceros.domain.party import PartyStatus


class PartyResponse(BaseModel):
    id: uuid.UUID
    kind: str
    legal_name: str
    tax_id: str
    status: str
    country: str | None
    city: str | None
    contact_name: str | None
    phone: str | None
    email: str | None
    notes: str | None
    main_material: str | None
    certifications: str | None
    rating: float | None
    segment: str | None
    preferred_material: str | None
    credit_limit: float | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, view: PartyView) -> PartyResponse:
        return cls(
            id=view.id,
            kind=view.kind,
            legal_name=view.legal_name,
            tax_id=view.tax_id,
            status=view.status,
            country=view.country,
            city=view.city,
            contact_name=view.contact_name,
            phone=view.phone,
            email=view.email,
            notes=view.notes,
            main_material=view.main_material,
            certifications=view.certifications,
            rating=view.rating,
            segment=view.segment,
            preferred_material=view.preferred_material,
            credit_limit=view.credit_limit,
            created_at=view.created_at,
        )


class PartyKpisResponse(BaseModel):
    total: int
    active: int
    evaluation: int
    inactive: int

    @classmethod
    def from_view(cls, view: PartyKpis) -> PartyKpisResponse:
        return cls(
            total=view.total,
            active=view.active,
            evaluation=view.evaluation,
            inactive=view.inactive,
        )


class CreatePartyRequest(BaseModel):
    legal_name: str = Field(min_length=1, max_length=200)
    tax_id: str = Field(min_length=1, max_length=40)
    status: PartyStatus = "active"
    country: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    contact_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    notes: str | None = None
    # Proveedor
    main_material: str | None = Field(default=None, max_length=80)
    certifications: str | None = Field(default=None, max_length=200)
    rating: float | None = Field(default=None, ge=0, le=5)
    # Cliente
    segment: str | None = Field(default=None, max_length=60)
    preferred_material: str | None = Field(default=None, max_length=80)
    credit_limit: float | None = Field(default=None, ge=0)

    def to_new_party(self) -> NewParty:
        return NewParty(
            legal_name=self.legal_name,
            tax_id=self.tax_id,
            status=self.status,
            country=self.country,
            city=self.city,
            contact_name=self.contact_name,
            phone=self.phone,
            email=self.email,
            notes=self.notes,
            main_material=self.main_material,
            certifications=self.certifications,
            rating=self.rating,
            segment=self.segment,
            preferred_material=self.preferred_material,
            credit_limit=self.credit_limit,
        )


class UpdatePartyRequest(BaseModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=200)
    tax_id: str | None = Field(default=None, min_length=1, max_length=40)
    status: PartyStatus | None = None
    country: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    contact_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    notes: str | None = None
    main_material: str | None = Field(default=None, max_length=80)
    certifications: str | None = Field(default=None, max_length=200)
    rating: float | None = Field(default=None, ge=0, le=5)
    segment: str | None = Field(default=None, max_length=60)
    preferred_material: str | None = Field(default=None, max_length=80)
    credit_limit: float | None = Field(default=None, ge=0)

    def to_patch(self) -> PartyPatch:
        # ``model_fields_set`` distingue "no enviado" de "enviado como null":
        # sólo se aplican los campos realmente presentes en el cuerpo (PATCH).
        fields = frozenset(self.model_fields_set)
        email = str(self.email) if self.email is not None else None
        return PartyPatch(
            legal_name=self.legal_name,
            tax_id=self.tax_id,
            status=self.status,
            country=self.country,
            city=self.city,
            contact_name=self.contact_name,
            phone=self.phone,
            email=email,
            notes=self.notes,
            main_material=self.main_material,
            certifications=self.certifications,
            rating=self.rating,
            segment=self.segment,
            preferred_material=self.preferred_material,
            credit_limit=self.credit_limit,
            fields_set=fields,
        )
