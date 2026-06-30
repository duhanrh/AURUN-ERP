"""Endpoints del Dashboard (``/dashboard``): resumen agregado (sección 7.16).

Lectura: ``dashboard:access``. Es solo lectura; agrega datos reales de los demás
módulos del tenant (RLS los acota automáticamente).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.presentation.router import build_accounting_service
from aurum.modules.auth.presentation.dependencies import require_permission
from aurum.modules.config.infrastructure.repositories import SqlAlchemyParametersRepository
from aurum.modules.dashboard.application.services import DashboardService
from aurum.modules.dashboard.infrastructure.spot_provider import get_spot_prices
from aurum.modules.dashboard.presentation.schemas import DashboardSummaryResponse
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
from aurum.modules.sales.infrastructure.repositories import SqlAlchemySalesOrderRepository
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_read = Depends(require_permission("dashboard:access"))


def _service(session: AsyncSession, tenant_id: uuid.UUID) -> DashboardService:
    return DashboardService(
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
        sales=SqlAlchemySalesOrderRepository(session),
        purchases=SqlAlchemyPurchaseOrderRepository(session),
        samples=SqlAlchemyQualitySampleRepository(session),
        accounting=build_accounting_service(session, tenant_id),
        parameters=SqlAlchemyParametersRepository(session),
        spot_provider=get_spot_prices,
    )


@router.get("/summary", response_model=DashboardSummaryResponse, dependencies=[_read])
async def dashboard_summary(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> DashboardSummaryResponse:
    return DashboardSummaryResponse.from_view(await _service(session, tenant_id).summary())
