"""Primitivas de seguridad: hashing de contraseñas y firma/verificación de JWT.

- **Contraseñas**: argon2 vía passlib (sección 10.1) — hashing lento con sal.
- **JWT**: RS256 (asimétrico, sección 10.4). La clave privada/pública se cargan de
  los ``*_path`` de ``Settings``. En ``local``/tests, si no hay claves
  configuradas, se genera un par RSA **efímero** en memoria (nunca en producción:
  allí la ausencia de claves es un error de configuración fatal).

Tokens:
- *access*: corta duración (~15 min), claims ``sub`` (user_id), ``tenant_id``,
  ``role``, ``perms``, ``jti``, ``type=access`` + ``iss``/``aud``/``exp``.
- *refresh*: el valor en claro es un secreto opaco; su ``jti`` y ``hash`` se
  persisten para rotación y revocación (ver ``RefreshToken``).
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from passlib.context import CryptContext

from aurum.shared.config import Settings, get_settings

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

JWT_ALGORITHM = "RS256"
JWT_ISSUER = "aurum-erp"
JWT_AUDIENCE = "aurum-erp-api"
TOKEN_TYPE_ACCESS = "access"


def hash_password(plain: str) -> str:
    return str(_pwd_context.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return bool(_pwd_context.verify(plain, hashed))


@dataclass(frozen=True, slots=True)
class KeyPair:
    private_pem: bytes
    public_pem: bytes


def _generate_ephemeral_keypair() -> KeyPair:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return KeyPair(private_pem, public_pem)


@lru_cache
def _load_keypair() -> KeyPair:
    settings = get_settings()
    priv_path = settings.jwt_private_key_path
    pub_path = settings.jwt_public_key_path
    if priv_path and pub_path:
        return KeyPair(Path(priv_path).read_bytes(), Path(pub_path).read_bytes())
    if settings.is_production:
        raise RuntimeError(
            "JWT_PRIVATE_KEY_PATH/JWT_PUBLIC_KEY_PATH son obligatorias en producción."
        )
    # Desarrollo/tests: par efímero estable durante el proceso (cacheado por lru_cache).
    return _generate_ephemeral_keypair()


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str | None
    permissions: tuple[str, ...]
    jti: str


class TokenService:
    """Emite y verifica tokens JWT de acceso y genera/valida refresh tokens opacos."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._keys = _load_keypair()

    # ── Access tokens (JWT firmado RS256) ──
    def issue_access_token(self, claims: AccessTokenClaims) -> str:
        now = datetime.now(tz=UTC)
        payload = {
            "sub": str(claims.user_id),
            "tenant_id": str(claims.tenant_id),
            "role": claims.role,
            "perms": list(claims.permissions),
            "jti": claims.jti,
            "type": TOKEN_TYPE_ACCESS,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(seconds=self._settings.jwt_access_ttl_seconds),
        }
        return jwt.encode(payload, self._keys.private_pem, algorithm=JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Verifica firma, ``iss``/``aud``/``exp`` y devuelve los claims tipados.

        Lanza ``jwt.InvalidTokenError`` (o subclase) si el token no es válido.
        """
        payload = jwt.decode(
            token,
            self._keys.public_pem,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            raise jwt.InvalidTokenError("Tipo de token inesperado")
        return AccessTokenClaims(
            user_id=uuid.UUID(payload["sub"]),
            tenant_id=uuid.UUID(payload["tenant_id"]),
            role=payload.get("role"),
            permissions=tuple(payload.get("perms", [])),
            jti=payload["jti"],
        )

    # ── Refresh tokens (secreto opaco; se persiste hash + jti) ──
    @staticmethod
    def generate_refresh_token() -> tuple[str, str, str]:
        """Devuelve ``(valor_en_claro, jti, hash)`` para un nuevo refresh token."""
        jti = uuid.uuid4().hex
        secret = secrets.token_urlsafe(48)
        raw = f"{jti}.{secret}"
        return raw, jti, TokenService.hash_refresh_token(raw)

    @staticmethod
    def hash_refresh_token(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @property
    def refresh_ttl_seconds(self) -> int:
        return self._settings.jwt_refresh_ttl_seconds
