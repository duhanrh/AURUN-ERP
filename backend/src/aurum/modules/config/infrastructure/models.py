"""Modelos ORM de Configuración: parámetros de negocio y módulos por tenant (+RLS).

La marca (``tenant_branding``) ya existe en el módulo de Tenants (sección 5.6); aquí
se añaden las otras dos entidades del panel de Configuración (sección 7.17):

- ``tenant_business_parameters`` (1:1): moneda, unidad de peso, umbrales de negocio.
- ``tenant_module_config``: una fila por módulo activable, con su bandera de activo.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aurum.shared.infrastructure.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TenantBusinessParameters(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_business_parameters"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_business_parameters_tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="USD")
    weight_unit: Mapped[str] = mapped_column(String(4), nullable=False, server_default="g")
    min_stock_g: Mapped[Decimal] = mapped_column(
        Numeric(16, 4), nullable=False, server_default="1000"
    )
    min_margin_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, server_default="5"
    )
    language: Mapped[str] = mapped_column(String(8), nullable=False, server_default="es")
    timezone: Mapped[str] = mapped_column(
        String(48), nullable=False, server_default="America/Bogota"
    )
    date_format: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="YYYY-MM-DD"
    )
    regulatory_entity: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")


class TenantModuleConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_module_config"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "module_key", name="uq_tenant_module_config_tenant_id_module_key"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    module_key: Mapped[str] = mapped_column(String(40), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
