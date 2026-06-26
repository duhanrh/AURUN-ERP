"""Pruebas de la lógica de permisos efectivos (dominio puro, sin BD)."""

from __future__ import annotations

from aurum.modules.users.domain.authorization import (
    compute_effective_permissions,
    has_permission,
)


def test_role_permissions_form_the_base() -> None:
    effective = compute_effective_permissions(["inventory:access", "sales:access"])
    assert effective == frozenset({"inventory:access", "sales:access"})


def test_granted_exception_adds_permission() -> None:
    effective = compute_effective_permissions(
        ["inventory:access"], granted_exceptions=["accounting:access"]
    )
    assert "accounting:access" in effective


def test_revoked_exception_removes_role_permission() -> None:
    effective = compute_effective_permissions(
        ["inventory:access", "sales:access"], revoked_exceptions=["sales:access"]
    )
    assert effective == frozenset({"inventory:access"})


def test_revocation_wins_over_grant() -> None:
    effective = compute_effective_permissions(
        [],
        granted_exceptions=["sales:access"],
        revoked_exceptions=["sales:access"],
    )
    assert "sales:access" not in effective


def test_has_permission_helper() -> None:
    effective = compute_effective_permissions(["users:manage"])
    assert has_permission(effective, "users:manage")
    assert not has_permission(effective, "audit:access")
