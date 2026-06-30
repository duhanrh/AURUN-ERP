"""Guardas de integridad del RBAC como **fuente de verdad en código** (sección 10.3).

No tocan la BD: validan que las definiciones de roles base solo referencien permisos
del catálogo (nada "hardcodeado" suelto), que los códigos sean únicos y que el
superusuario realmente abarque todo el catálogo. Si alguien añade un permiso a un rol
sin registrarlo en el catálogo, este test falla antes de llegar a producción.
"""

from __future__ import annotations

from aurum.modules.users.domain.permissions import (
    BASE_ROLES,
    DEFAULT_ADMIN_ROLE_SLUG,
    PERMISSION_CATALOG,
    ROLE_SUPERUSUARIO,
)


def test_permission_codes_are_unique() -> None:
    codes = [p.code for p in PERMISSION_CATALOG]
    assert len(codes) == len(set(codes)), "Hay códigos de permiso duplicados en el catálogo."


def test_every_role_permission_is_in_catalog() -> None:
    catalog = {p.code for p in PERMISSION_CATALOG}
    for role in BASE_ROLES:
        for perm in role.permissions:
            assert perm.code in catalog, (
                f"El rol '{role.slug}' referencia '{perm.code}', que no está en el catálogo."
            )


def test_superuser_grants_all_and_is_default_admin() -> None:
    assert ROLE_SUPERUSUARIO.grants_all is True
    assert ROLE_SUPERUSUARIO.slug == DEFAULT_ADMIN_ROLE_SLUG


def test_role_codes_have_no_duplicates_within_a_role() -> None:
    for role in BASE_ROLES:
        codes = [p.code for p in role.permissions]
        assert len(codes) == len(set(codes)), f"El rol '{role.slug}' repite permisos."
