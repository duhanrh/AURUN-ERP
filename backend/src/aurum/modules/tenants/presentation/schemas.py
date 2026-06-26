"""Esquemas Pydantic de la API de plataforma (provisionamiento de tenants)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

_SUBDOMAIN_PATTERN = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"


class ProvisionTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    subdomain: str = Field(min_length=1, max_length=63, pattern=_SUBDOMAIN_PATTERN)
    admin_email: EmailStr
    admin_full_name: str = Field(min_length=1, max_length=160)
    subscription_plan: str = Field(default="free", max_length=40)
    admin_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("subdomain")
    @classmethod
    def _lowercase(cls, value: str) -> str:
        return value.lower()


class ProvisionTenantResponse(BaseModel):
    tenant_id: uuid.UUID
    subdomain: str
    admin_email: str
    admin_user_id: uuid.UUID
    initial_password: str
    roles_created: int
