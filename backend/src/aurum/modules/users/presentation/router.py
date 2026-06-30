"""Endpoints de Usuarios y Roles (Configuración → Usuarios y Roles, sección 7.2).

Todos protegidos por el permiso ``users:manage`` (RBAC, sección 10.2): la
comprobación es de servidor, no solo de UI.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.audit.domain.actions import (
    USER_CREATE,
    USER_DELETE,
    USER_RESTORE,
    USER_UPDATE,
)
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.infrastructure.security import hash_password
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.modules.users.application.dto import NewUser
from aurum.modules.users.application.services import UserService
from aurum.modules.users.domain.permissions import PERM_USERS_MANAGE
from aurum.modules.users.infrastructure.repositories import (
    SqlAlchemyPermissionRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from aurum.modules.users.presentation.schemas import (
    CreateUserRequest,
    RoleResponse,
    UpdateUserRequest,
    UserResponse,
)
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/users", tags=["users"])

_guard = require_permission(PERM_USERS_MANAGE.code)


def _build_service(session: AsyncSession, tenant_id: uuid.UUID) -> UserService:
    return UserService(
        tenant_id=tenant_id,
        users=SqlAlchemyUserRepository(session),
        roles=SqlAlchemyRoleRepository(session),
        permissions=SqlAlchemyPermissionRepository(session),
        password_hasher=hash_password,
    )


@router.get("", response_model=list[UserResponse], dependencies=[Depends(_guard)])
async def list_users(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    include_deleted: bool = Query(default=False),
) -> list[UserResponse]:
    views = await _build_service(session, tenant_id).list_users(include_deleted=include_deleted)
    return [UserResponse.from_view(v) for v in views]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_guard)],
)
async def create_user(
    payload: CreateUserRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_guard),
) -> UserResponse:
    view = await _build_service(session, tenant_id).create_user(
        NewUser(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role_slug=payload.role_slug,
            granted_permissions=tuple(payload.granted_permissions),
            revoked_permissions=tuple(payload.revoked_permissions),
        )
    )
    await record_event(
        session,
        tenant_id,
        action=USER_CREATE,
        entity_type="user",
        entity_id=view.id,
        principal=principal,
        request=request,
        changes={"email": view.email, "role": payload.role_slug},
    )
    return UserResponse.from_view(view)


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(_guard)])
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> UserResponse:
    view = await _build_service(session, tenant_id).get_user(user_id)
    return UserResponse.from_view(view)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(_guard)])
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_guard),
) -> UserResponse:
    view = await _build_service(session, tenant_id).update_user(user_id, payload.to_patch())
    await record_event(
        session,
        tenant_id,
        action=USER_UPDATE,
        entity_type="user",
        entity_id=user_id,
        principal=principal,
        request=request,
        changes=payload.model_dump(exclude_unset=True, exclude={"password"}),
    )
    return UserResponse.from_view(view)


@router.delete("/{user_id}", response_model=UserResponse, dependencies=[Depends(_guard)])
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_guard),
) -> UserResponse:
    view = await _build_service(session, tenant_id).delete_user(
        user_id, current_user_id=principal.user_id
    )
    await record_event(
        session,
        tenant_id,
        action=USER_DELETE,
        entity_type="user",
        entity_id=user_id,
        principal=principal,
        request=request,
        changes={"email": view.email},
    )
    return UserResponse.from_view(view)


@router.post("/{user_id}/restore", response_model=UserResponse, dependencies=[Depends(_guard)])
async def restore_user(
    user_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = Depends(_guard),
) -> UserResponse:
    view = await _build_service(session, tenant_id).restore_user(user_id)
    await record_event(
        session,
        tenant_id,
        action=USER_RESTORE,
        entity_type="user",
        entity_id=user_id,
        principal=principal,
        request=request,
    )
    return UserResponse.from_view(view)


roles_router = APIRouter(prefix="/roles", tags=["roles"])


@roles_router.get("", response_model=list[RoleResponse], dependencies=[Depends(_guard)])
async def list_roles(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[RoleResponse]:
    views = await _build_service(session, tenant_id).list_roles()
    return [RoleResponse.from_view(v) for v in views]
