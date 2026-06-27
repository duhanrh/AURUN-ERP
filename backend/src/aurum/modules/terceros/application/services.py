"""Casos de uso del módulo de Terceros (Clientes/Proveedores).

Cada instancia opera sobre un ``kind`` fijo (cliente o proveedor), de modo que la
presentación monta dos routers (``/customers`` y ``/suppliers``) sobre el mismo
servicio sin duplicar lógica. La verificación de permisos vive en presentación
(``customers:manage`` / ``suppliers:manage``); aquí van las invariantes de negocio.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from aurum.modules.terceros.application.dto import (
    NewParty,
    PartyKpis,
    PartyPatch,
    PartyView,
)
from aurum.modules.terceros.application.ports import PartyRepository
from aurum.modules.terceros.domain.party import (
    DEFAULT_PARTY_STATUS,
    RATING_MAX,
    RATING_MIN,
    PartyKind,
)
from aurum.modules.terceros.infrastructure.models import Party
from aurum.shared.errors import ConflictError, DomainError, NotFoundError

# Campos que sólo aplican a proveedores / clientes; al cambiar de tipo no se usan,
# pero el servicio nunca cambia de tipo, así que basta validarlos por kind.
_SUPPLIER_ONLY = ("main_material", "certifications", "rating")
_CUSTOMER_ONLY = ("segment", "preferred_material", "credit_limit")


class ValidationError(DomainError):
    status_code = 422
    error_code = "validation_error"


def _to_view(party: Party) -> PartyView:
    return PartyView(
        id=party.id,
        kind=party.kind,  # type: ignore[arg-type]
        legal_name=party.legal_name,
        tax_id=party.tax_id,
        status=party.status,  # type: ignore[arg-type]
        country=party.country,
        city=party.city,
        contact_name=party.contact_name,
        phone=party.phone,
        email=party.email,
        notes=party.notes,
        main_material=party.main_material,
        certifications=party.certifications,
        rating=float(party.rating) if party.rating is not None else None,
        segment=party.segment,
        preferred_material=party.preferred_material,
        credit_limit=float(party.credit_limit) if party.credit_limit is not None else None,
        created_at=party.created_at,
    )


class PartyService:
    """Gestión del maestro de terceros de un ``kind`` dentro del tenant activo."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        kind: PartyKind,
        parties: PartyRepository,
    ) -> None:
        self._tenant_id = tenant_id
        self._kind = kind
        self._parties = parties

    async def list(self) -> list[PartyView]:
        return [_to_view(p) for p in await self._parties.list_by_kind(self._kind)]

    async def kpis(self) -> PartyKpis:
        counts = await self._parties.count_by_status(self._kind)
        return PartyKpis(
            total=sum(counts.values()),
            active=counts.get("active", 0),
            evaluation=counts.get("evaluation", 0),
            inactive=counts.get("inactive", 0),
        )

    async def get(self, party_id: uuid.UUID) -> PartyView:
        party = await self._parties.get(self._kind, party_id)
        if party is None:
            raise NotFoundError("Tercero no encontrado.")
        return _to_view(party)

    async def create(self, data: NewParty) -> PartyView:
        tax_id = data.tax_id.strip()
        if not tax_id:
            raise ValidationError("El NIT/documento es obligatorio.")
        if data.rating is not None:
            self._validate_rating(data.rating)
        if await self._parties.exists_tax_id(self._kind, tax_id):
            raise ConflictError(
                "Ya existe un tercero de este tipo con ese NIT/documento en el tenant."
            )

        party = Party(
            tenant_id=self._tenant_id,
            kind=self._kind,
            legal_name=data.legal_name.strip(),
            tax_id=tax_id,
            status=data.status or DEFAULT_PARTY_STATUS,
            country=data.country,
            city=data.city,
            contact_name=data.contact_name,
            phone=data.phone,
            email=data.email,
            notes=data.notes,
        )
        self._apply_kind_fields(party, data)
        await self._parties.add(party)
        return _to_view(party)

    async def update(self, party_id: uuid.UUID, patch: PartyPatch) -> PartyView:
        party = await self._parties.get(self._kind, party_id)
        if party is None:
            raise NotFoundError("Tercero no encontrado.")

        fields = patch.fields_set
        if "rating" in fields and patch.rating is not None:
            self._validate_rating(patch.rating)
        if "tax_id" in fields:
            new_tax = (patch.tax_id or "").strip()
            if not new_tax:
                raise ValidationError("El NIT/documento es obligatorio.")
            if new_tax != party.tax_id and await self._parties.exists_tax_id(
                self._kind, new_tax, exclude_id=party.id
            ):
                raise ConflictError(
                    "Ya existe un tercero de este tipo con ese NIT/documento en el tenant."
                )
            party.tax_id = new_tax

        if "legal_name" in fields and patch.legal_name is not None:
            party.legal_name = patch.legal_name.strip()
        for attr in (
            "status",
            "country",
            "city",
            "contact_name",
            "phone",
            "email",
            "notes",
        ):
            if attr in fields:
                setattr(party, attr, getattr(patch, attr))

        self._apply_kind_fields_patch(party, patch)
        return _to_view(party)

    # ── helpers ──
    def _apply_kind_fields(self, party: Party, data: NewParty) -> None:
        if self._kind == "supplier":
            party.main_material = data.main_material
            party.certifications = data.certifications
            party.rating = _decimal(data.rating)
        else:
            party.segment = data.segment
            party.preferred_material = data.preferred_material
            party.credit_limit = _decimal(data.credit_limit)

    def _apply_kind_fields_patch(self, party: Party, patch: PartyPatch) -> None:
        allowed = _SUPPLIER_ONLY if self._kind == "supplier" else _CUSTOMER_ONLY
        for attr in allowed:
            if attr in patch.fields_set:
                value = getattr(patch, attr)
                if attr in ("rating", "credit_limit"):
                    value = _decimal(value)
                setattr(party, attr, value)

    @staticmethod
    def _validate_rating(rating: float) -> None:
        if not RATING_MIN <= rating <= RATING_MAX:
            raise ValidationError(f"El rating debe estar entre {RATING_MIN} y {RATING_MAX}.")


def _decimal(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None
