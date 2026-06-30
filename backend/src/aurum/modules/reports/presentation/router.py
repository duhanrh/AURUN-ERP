"""Endpoints de Reportes (``/reports``): catálogo, vista previa y exportación (7.15).

Lectura: ``reports:access``. La vista previa devuelve la tabla en JSON; la
exportación entrega un CSV real descargable con cabecera de marca del tenant.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.presentation.router import build_accounting_service
from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.modules.config.infrastructure.repositories import (
    SqlAlchemyBrandingRepository,
    SqlAlchemyParametersRepository,
)
from aurum.modules.dashboard.infrastructure.spot_provider import get_spot_prices
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.purchasing.infrastructure.repositories import (
    SqlAlchemyPurchaseOrderRepository,
)
from aurum.modules.quality.infrastructure.repositories import (
    SqlAlchemyQualitySampleRepository,
)
from aurum.modules.reports.application.dto import ReportTable
from aurum.modules.reports.application.services import ReportsService
from aurum.modules.reports.presentation.schemas import (
    ReportTableResponse,
    ReportTypeResponse,
)
from aurum.modules.sales.infrastructure.repositories import SqlAlchemySalesOrderRepository
from aurum.modules.transformation.infrastructure.repositories import (
    SqlAlchemyTransformationOrderRepository,
)
from aurum.shared.dependencies import get_session, require_tenant_id
from aurum.shared.export import (
    EXPORT_FORMATS,
    ExportDoc,
    ExportFormat,
    ExportSummary,
    export_response,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_read = Depends(require_permission("reports:access"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> ReportsService:
    return ReportsService(
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
        sales=SqlAlchemySalesOrderRepository(session),
        purchases=SqlAlchemyPurchaseOrderRepository(session),
        transformations=SqlAlchemyTransformationOrderRepository(session),
        samples=SqlAlchemyQualitySampleRepository(session),
        accounting=build_accounting_service(session, tenant_id),
        branding=SqlAlchemyBrandingRepository(session),
        parameters=SqlAlchemyParametersRepository(session),
        spot_provider=get_spot_prices,
    )


@router.get("", response_model=list[ReportTypeResponse], dependencies=[_read])
async def list_reports(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[ReportTypeResponse]:
    return [ReportTypeResponse.from_view(v) for v in _service(session, tenant_id).list_types()]


@router.get("/{key}", response_model=ReportTableResponse, dependencies=[_read])
async def preview_report(
    key: str,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> ReportTableResponse:
    table = await _service(session, tenant_id).generate(key)
    return ReportTableResponse.from_view(table)


def _to_export_doc(table: ReportTable) -> ExportDoc:
    return ExportDoc(
        brand_name=table.brand_name,
        title=table.title,
        document_number=table.document_number,
        generated_at=table.generated_at,
        columns=list(table.columns),
        rows=[list(r) for r in table.rows],
        summary=[ExportSummary(label=s.label, value=s.value) for s in table.summary],
    )


@router.get("/{key}/export", dependencies=[_read])
async def export_report(
    key: str,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    fmt: ExportFormat = Query(default="csv", alias="format"),
) -> Response:
    if fmt not in EXPORT_FORMATS:
        fmt = "csv"
    table = await _service(session, tenant_id).generate(key)
    return export_response(
        _to_export_doc(table), fmt, filename_base=f"{key}_{table.document_number}"
    )
