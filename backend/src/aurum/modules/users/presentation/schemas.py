"""Esquemas Pydantic de la API de Usuarios y Roles (sección 7.2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from aurum.modules.users.application.dto import RoleView, UserView


class RoleResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    is_system: bool
    permissions: list[str]

    @classmethod
    def from_view(cls, view: RoleView) -> RoleResponse:
        return cls(
            id=view.id,
            slug=view.slug,
            name=view.name,
            description=view.description,
            is_system=view.is_system,
            permissions=list(view.permission_codes),
        )


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    role: RoleResponse | None
    permissions: list[str]
    last_login_at: datetime | None
    created_at: datetime | None

    @classmethod
    def from_view(cls, view: UserView) -> UserResponse:
        return cls(
            id=view.id,
            email=view.email,
            full_name=view.full_name,
            is_active=view.is_active,
            role=RoleResponse.from_view(view.role) if view.role else None,
            permissions=sorted(view.effective_permissions),
            last_login_at=view.last_login_at,
            created_at=view.created_at,
        )


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role_slug: str = Field(min_length=1, max_length=40)
    granted_permissions: list[str] = Field(default_factory=list)
    revoked_permissions: list[str] = Field(default_factory=list)
