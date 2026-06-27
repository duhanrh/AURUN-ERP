"""Dominio de API Keys: scopes, generación y verificación (sección 7.19).

Las API Keys autentican integraciones externas con **scopes explícitos** y de solo
lectura; nunca usan el JWT de sesión interactiva. La clave se entrega una sola vez
al crearla; en BD se guarda únicamente el ``hash`` del secreto (SHA-256) más un
``prefix`` público para localizarla, de modo que una fuga de la tabla no revela las
claves utilizables.

Formato: ``aurum_<prefix>.<secret>`` (el ``.`` separa prefijo de secreto; el secreto
es ``token_urlsafe`` que solo usa ``[A-Za-z0-9_-]``, sin puntos).
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Literal, get_args

Scope = Literal["inventory:read", "reports:read"]
SCOPES: tuple[Scope, ...] = get_args(Scope)

_KEY_PREFIX = "aurum"


def generate_api_key() -> tuple[str, str, str]:
    """Devuelve ``(full_key, prefix, secret_hash)``. ``full_key`` se muestra una vez."""
    prefix = secrets.token_hex(6)
    secret = secrets.token_urlsafe(32)
    full_key = f"{_KEY_PREFIX}_{prefix}.{secret}"
    return full_key, prefix, hash_secret(secret)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def parse_api_key(full_key: str) -> tuple[str, str] | None:
    """Extrae ``(prefix, secret)`` de una clave; ``None`` si el formato es inválido."""
    if not full_key.startswith(f"{_KEY_PREFIX}_"):
        return None
    body = full_key[len(_KEY_PREFIX) + 1 :]
    prefix, sep, secret = body.partition(".")
    if not sep or not prefix or not secret:
        return None
    return prefix, secret


def verify_secret(secret: str, secret_hash: str) -> bool:
    return secrets.compare_digest(hash_secret(secret), secret_hash)


def valid_scopes(scopes: list[str]) -> bool:
    return all(s in SCOPES for s in scopes) and len(scopes) > 0
