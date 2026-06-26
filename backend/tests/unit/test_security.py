"""Pruebas de las primitivas de seguridad (hashing y JWT), sin BD."""

from __future__ import annotations

import uuid

import jwt
import pytest

from aurum.modules.auth.infrastructure.security import (
    AccessTokenClaims,
    TokenService,
    hash_password,
    verify_password,
)


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("s3cr3t-pass")
    assert hashed != "s3cr3t-pass"
    assert verify_password("s3cr3t-pass", hashed)
    assert not verify_password("otra", hashed)


def test_access_token_roundtrip_preserves_claims() -> None:
    service = TokenService()
    user_id, tenant_id = uuid.uuid4(), uuid.uuid4()
    token = service.issue_access_token(
        AccessTokenClaims(
            user_id=user_id,
            tenant_id=tenant_id,
            role="superusuario",
            permissions=("users:manage", "inventory:access"),
            jti="abc123",
        )
    )
    claims = service.decode_access_token(token)
    assert claims.user_id == user_id
    assert claims.tenant_id == tenant_id
    assert claims.role == "superusuario"
    assert set(claims.permissions) == {"users:manage", "inventory:access"}
    assert claims.jti == "abc123"


def test_decode_rejects_garbage() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        TokenService().decode_access_token("no-es-un-jwt")


def test_refresh_token_hash_is_deterministic_and_parts_match() -> None:
    raw, jti, token_hash = TokenService.generate_refresh_token()
    assert raw.split(".", 1)[0] == jti
    assert TokenService.hash_refresh_token(raw) == token_hash
    # Dos tokens distintos no colisionan.
    other_raw, _, _ = TokenService.generate_refresh_token()
    assert other_raw != raw
