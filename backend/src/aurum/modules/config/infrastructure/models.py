"""Modelos ORM de Configuración: parámetros de negocio y módulos por tenant (+RLS).

La marca (``tenant_branding``) ya existe en el módulo de Tenants (sección 5.6); aquí
se añaden las otras dos entidades del panel de Configuración (sección 7.17):

- ``tenant_business_parameters`` (1:1): moneda, unidad de peso, umbrales de negocio.
- ``tenant_module_config``: una fila por módulo activable, con su bandera de activo.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aurum.shared.infrastructure.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


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


class UnitOfMeasure(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Unidad de medida de peso configurable por tenant (sección 7.17).

    ``grams_factor`` = gramos que equivalen a 1 unidad; el gramo es la base
    (factor 1, ``is_base=True``). El ``code`` es único por tenant entre las
    unidades vigentes (índice parcial ``WHERE deleted_at IS NULL``), de modo que
    reutilizar el código de una unidad eliminada no choca.
    """

    __tablename__ = "units_of_measure"
    __table_args__ = (
        Index(
            "uq_units_of_measure_tenant_id_code",
            "tenant_id",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    grams_factor: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class Currency(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Moneda configurable por tenant (sección 7.17).

    Una sola moneda lleva ``is_base=True`` (la del negocio). El ``code`` (ISO,
    p. ej. ``COP``/``USD``) es único por tenant entre las monedas vigentes.
    """

    __tablename__ = "currencies"
    __table_args__ = (
        Index(
            "uq_currencies_tenant_id_code",
            "tenant_id",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    decimals: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class TenantCompany(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Datos del comercio/empresa del tenant (1:1), usados en documentos impresos.

    Distinto de ``tenant_branding`` (identidad visual): aquí van los datos
    legales/fiscales (razón social, NIT, dirección, contacto) que encabezan las
    facturas y recibos.
    """

    __tablename__ = "tenant_company"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_company_tenant_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(160), nullable=False, server_default="")
    trade_name: Mapped[str] = mapped_column(String(160), nullable=False, server_default="")
    tax_id: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    tax_regime: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    address: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    city: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    phone: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    email: Mapped[str] = mapped_column(String(160), nullable=False, server_default="")
    website: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
