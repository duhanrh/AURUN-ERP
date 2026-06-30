"""Catálogo de acciones auditadas (sección 7.18).

Las acciones son identificadores estables ``entidad.operación``. Como mínimo se
auditan (sección 7.18): alta de usuarios, cambios de configuración (marca, módulos,
parámetros), aprobación de órdenes de compra, asientos contables manuales y accesos
fallidos.
"""

from __future__ import annotations

USER_CREATE = "user.create"
USER_UPDATE = "user.update"
USER_DELETE = "user.delete"
USER_RESTORE = "user.restore"
PARTY_DELETE = "party.delete"
PARTY_RESTORE = "party.restore"
MATERIAL_CREATE = "material.create"
MATERIAL_UPDATE = "material.update"
MATERIAL_DELETE = "material.delete"
MATERIAL_RESTORE = "material.restore"
CONFIG_BRANDING_UPDATE = "config.branding.update"
CONFIG_BRANDING_RESET = "config.branding.reset"
CONFIG_PARAMETERS_UPDATE = "config.parameters.update"
CONFIG_MODULE_TOGGLE = "config.module.toggle"
UNIT_CREATE = "unit.create"
UNIT_UPDATE = "unit.update"
UNIT_DELETE = "unit.delete"
UNIT_RESTORE = "unit.restore"
CURRENCY_CREATE = "currency.create"
CURRENCY_UPDATE = "currency.update"
CURRENCY_DELETE = "currency.delete"
CURRENCY_RESTORE = "currency.restore"
CURRENCY_SET_BASE = "currency.set_base"
CONFIG_COMPANY_UPDATE = "config.company.update"
PURCHASE_ORDER_APPROVE = "purchase_order.approve"
# Documentos de operación (Ola 2): edición y baja/alta lógica.
LOT_UPDATE = "lot.update"
LOT_DELETE = "lot.delete"
LOT_RESTORE = "lot.restore"
PURCHASE_ORDER_UPDATE = "purchase_order.update"
PURCHASE_ORDER_DELETE = "purchase_order.delete"
PURCHASE_ORDER_RESTORE = "purchase_order.restore"
SALES_ORDER_UPDATE = "sales_order.update"
SALES_ORDER_DELETE = "sales_order.delete"
SALES_ORDER_RESTORE = "sales_order.restore"
TRANSFORMATION_UPDATE = "transformation.update"
TRANSFORMATION_DELETE = "transformation.delete"
TRANSFORMATION_RESTORE = "transformation.restore"
SAMPLE_UPDATE = "sample.update"
SAMPLE_DELETE = "sample.delete"
SAMPLE_RESTORE = "sample.restore"
ACCOUNTING_MANUAL_ENTRY = "accounting.manual_entry"
AUTH_LOGIN_FAILED = "auth.login_failed"
