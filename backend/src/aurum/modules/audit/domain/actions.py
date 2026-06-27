"""Catálogo de acciones auditadas (sección 7.18).

Las acciones son identificadores estables ``entidad.operación``. Como mínimo se
auditan (sección 7.18): alta de usuarios, cambios de configuración (marca, módulos,
parámetros), aprobación de órdenes de compra, asientos contables manuales y accesos
fallidos.
"""

from __future__ import annotations

USER_CREATE = "user.create"
CONFIG_BRANDING_UPDATE = "config.branding.update"
CONFIG_BRANDING_RESET = "config.branding.reset"
CONFIG_PARAMETERS_UPDATE = "config.parameters.update"
CONFIG_MODULE_TOGGLE = "config.module.toggle"
PURCHASE_ORDER_APPROVE = "purchase_order.approve"
ACCOUNTING_MANUAL_ENTRY = "accounting.manual_entry"
AUTH_LOGIN_FAILED = "auth.login_failed"
