"""Cálculo de permisos efectivos de un usuario (lógica de dominio pura).

Permisos efectivos = (permisos del rol) ∪ (excepciones que otorgan) − (excepciones
que revocan). Las excepciones por usuario (sección 10.3) tienen prioridad sobre el
rol, permitiendo el patrón de la maqueta (checklist de módulos por usuario).

Función pura, sin dependencias de framework ni de base de datos: trivial de testear.
"""

from __future__ import annotations

from collections.abc import Iterable


def compute_effective_permissions(
    role_permission_codes: Iterable[str],
    granted_exceptions: Iterable[str] = (),
    revoked_exceptions: Iterable[str] = (),
) -> frozenset[str]:
    """Combina permisos de rol con excepciones por usuario.

    Las revocaciones se aplican al final, de modo que revocar siempre gana frente a
    un permiso del rol o una excepción que otorga el mismo código.
    """
    effective = set(role_permission_codes) | set(granted_exceptions)
    effective -= set(revoked_exceptions)
    return frozenset(effective)


def has_permission(effective: Iterable[str], required: str) -> bool:
    return required in set(effective)
