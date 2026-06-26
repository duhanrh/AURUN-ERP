"""DTOs del módulo de Autenticación."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Par de tokens emitido tras login o rotación de refresh."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"  # noqa: S105 — etiqueta del esquema, no un secreto
