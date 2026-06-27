"""Catálogo de permisos y roles base de la plataforma (secciones 10.2/10.3).

Este módulo es la **única fuente de verdad** del RBAC: lo consumen tanto el
sembrado (seeds) del provisionamiento de tenants (sección 5.7) como las
comprobaciones de autorización en la capa de aplicación. Los permisos forman un
catálogo de plataforma versionado en código —no editable libremente por tenant—
para garantizar consistencia entre todos los tenants (sección 10.3).

Granularidad de Fase 2: permisos de **acceso a nivel de módulo** (``<modulo>:access``)
más algunas acciones sensibles ya visibles en la maqueta (aprobar OC, asiento
contable manual, gestión de usuarios). Acciones más finas (``inventory:write``…)
se añaden al catálogo en fases posteriores sin romper compatibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionDef:
    """Definición inmutable de un permiso del catálogo de plataforma."""

    code: str
    """Identificador estable ``recurso:accion`` (p. ej. ``inventory:access``)."""
    resource: str
    action: str
    description: str


def _access(resource: str, label: str) -> PermissionDef:
    return PermissionDef(f"{resource}:access", resource, "access", f"Acceder al módulo {label}")


# ── Permisos de acceso por módulo (alineados con la navegación de la maqueta) ──
PERM_DASHBOARD = _access("dashboard", "Dashboard")
PERM_INVENTORY = _access("inventory", "Inventario")
PERM_PURCHASING = _access("purchasing", "Compras")
PERM_SALES = _access("sales", "Ventas")
PERM_TRANSFORMATION = _access("transformation", "Transformación")
PERM_SUPPLIERS = _access("suppliers", "Proveedores")
PERM_CUSTOMERS = _access("customers", "Clientes")
PERM_QUALITY = _access("quality", "Calidad / Laboratorio")
PERM_ACCOUNTING = _access("accounting", "Contabilidad")
PERM_REPORTS = _access("reports", "Reportes")
PERM_CONFIGURATION = _access("configuration", "Configuración")
PERM_AUDIT = _access("audit", "Auditoría")

# ── Permisos de acción sensibles (ya insinuados en la maqueta) ──
PERM_PURCHASE_ORDER_APPROVE = PermissionDef(
    "purchase_order:approve", "purchase_order", "approve", "Aprobar órdenes de compra"
)
PERM_ACCOUNTING_MANUAL_ENTRY = PermissionDef(
    "accounting:manual_entry", "accounting", "manual_entry", "Registrar asientos contables manuales"
)
PERM_USERS_MANAGE = PermissionDef(
    "users:manage", "users", "manage", "Gestionar usuarios y roles del tenant"
)
PERM_CUSTOMERS_MANAGE = PermissionDef(
    "customers:manage", "customers", "manage", "Crear y editar clientes (terceros)"
)
PERM_SUPPLIERS_MANAGE = PermissionDef(
    "suppliers:manage", "suppliers", "manage", "Crear y editar proveedores (terceros)"
)
PERM_INVENTORY_MANAGE = PermissionDef(
    "inventory:manage", "inventory", "manage", "Registrar y ajustar lotes de inventario"
)
PERM_PURCHASING_MANAGE = PermissionDef(
    "purchasing:manage", "purchasing", "manage", "Crear órdenes de compra"
)
PERM_SALES_MANAGE = PermissionDef(
    "sales:manage", "sales", "manage", "Crear órdenes de venta"
)
PERM_TRANSFORMATION_MANAGE = PermissionDef(
    "transformation:manage", "transformation", "manage", "Gestionar órdenes de transformación"
)
PERM_QUALITY_MANAGE = PermissionDef(
    "quality:manage", "quality", "manage", "Registrar muestras de laboratorio"
)

PERMISSION_CATALOG: tuple[PermissionDef, ...] = (
    PERM_DASHBOARD,
    PERM_INVENTORY,
    PERM_PURCHASING,
    PERM_SALES,
    PERM_TRANSFORMATION,
    PERM_SUPPLIERS,
    PERM_CUSTOMERS,
    PERM_QUALITY,
    PERM_ACCOUNTING,
    PERM_REPORTS,
    PERM_CONFIGURATION,
    PERM_AUDIT,
    PERM_PURCHASE_ORDER_APPROVE,
    PERM_ACCOUNTING_MANUAL_ENTRY,
    PERM_USERS_MANAGE,
    PERM_CUSTOMERS_MANAGE,
    PERM_SUPPLIERS_MANAGE,
    PERM_INVENTORY_MANAGE,
    PERM_PURCHASING_MANAGE,
    PERM_SALES_MANAGE,
    PERM_TRANSFORMATION_MANAGE,
    PERM_QUALITY_MANAGE,
)

# Acceso a todos los módulos visibles del ERP (sin Auditoría, reservada a roles altos).
_ALL_MODULE_ACCESS: tuple[PermissionDef, ...] = (
    PERM_DASHBOARD,
    PERM_INVENTORY,
    PERM_PURCHASING,
    PERM_SALES,
    PERM_TRANSFORMATION,
    PERM_SUPPLIERS,
    PERM_CUSTOMERS,
    PERM_QUALITY,
    PERM_ACCOUNTING,
    PERM_REPORTS,
    PERM_CONFIGURATION,
)


@dataclass(frozen=True, slots=True)
class RoleDef:
    """Definición de un rol base del sistema (sembrado por tenant)."""

    slug: str
    name: str
    description: str
    permissions: tuple[PermissionDef, ...]
    """Permisos efectivos; ``()`` con ``grants_all`` => comodín (todos)."""
    grants_all: bool = False


# ── Roles base sembrados en cada tenant nuevo (secciones 5.7 / 10.2) ──
ROLE_SUPERUSUARIO = RoleDef(
    "superusuario",
    "Superusuario",
    "Acceso total a la plataforma del tenant.",
    PERMISSION_CATALOG,
    grants_all=True,
)
ROLE_GERENTE = RoleDef(
    "gerente",
    "Gerente",
    "Gestión integral del negocio: todos los módulos y aprobaciones.",
    (
        *_ALL_MODULE_ACCESS,
        PERM_PURCHASE_ORDER_APPROVE,
        PERM_USERS_MANAGE,
        PERM_CUSTOMERS_MANAGE,
        PERM_SUPPLIERS_MANAGE,
        PERM_INVENTORY_MANAGE,
        PERM_PURCHASING_MANAGE,
        PERM_SALES_MANAGE,
        PERM_TRANSFORMATION_MANAGE,
        PERM_QUALITY_MANAGE,
    ),
)
ROLE_OPERATIVO = RoleDef(
    "operativo",
    "Operativo",
    "Operación diaria: inventario, compras, ventas, transformación.",
    (
        PERM_DASHBOARD,
        PERM_INVENTORY,
        PERM_PURCHASING,
        PERM_SALES,
        PERM_TRANSFORMATION,
        PERM_SUPPLIERS,
        PERM_CUSTOMERS,
        PERM_QUALITY,
        PERM_CUSTOMERS_MANAGE,
        PERM_SUPPLIERS_MANAGE,
        PERM_INVENTORY_MANAGE,
        PERM_PURCHASING_MANAGE,
        PERM_SALES_MANAGE,
        PERM_TRANSFORMATION_MANAGE,
    ),
)
ROLE_FINANZAS = RoleDef(
    "finanzas",
    "Finanzas",
    "Contabilidad, cartera y reportes financieros.",
    (
        PERM_DASHBOARD,
        PERM_ACCOUNTING,
        PERM_ACCOUNTING_MANUAL_ENTRY,
        PERM_REPORTS,
        PERM_SALES,
        PERM_PURCHASING,
        PERM_CUSTOMERS,
        PERM_SUPPLIERS,
        PERM_CUSTOMERS_MANAGE,
        PERM_SUPPLIERS_MANAGE,
        PERM_PURCHASING_MANAGE,
        PERM_SALES_MANAGE,
    ),
)
ROLE_LABORATORIO = RoleDef(
    "laboratorio",
    "Laboratorio",
    "Control de calidad y análisis de laboratorio.",
    (PERM_DASHBOARD, PERM_QUALITY, PERM_QUALITY_MANAGE, PERM_INVENTORY),
)
ROLE_SOLO_LECTURA = RoleDef(
    "solo_lectura",
    "Solo lectura",
    "Visualización de todos los módulos sin capacidad de acción.",
    _ALL_MODULE_ACCESS,
)

BASE_ROLES: tuple[RoleDef, ...] = (
    ROLE_SUPERUSUARIO,
    ROLE_GERENTE,
    ROLE_OPERATIVO,
    ROLE_FINANZAS,
    ROLE_LABORATORIO,
    ROLE_SOLO_LECTURA,
)

DEFAULT_ADMIN_ROLE_SLUG = ROLE_SUPERUSUARIO.slug
