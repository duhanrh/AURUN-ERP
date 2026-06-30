"""API pública versionada (``/public/v1``) autenticada por API Key (sección 7.19).

Subconjunto **curado de solo lectura** de la API interna. Cada endpoint exige un
scope explícito de la API Key; el tenant se resuelve de la clave y las respuestas
pasan por RLS. Documentada automáticamente en OpenAPI (``/docs``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.presentation.router import build_accounting_service
from aurum.modules.config.infrastructure.repositories import (
    SqlAlchemyBrandingRepository,
    SqlAlchemyParametersRepository,
)
from aurum.modules.dashboard.infrastructure.spot_provider import get_spot_prices
from aurum.modules.inventory.application.services import InventoryService
from aurum.modules.inventory.infrastructure.repositories import (
    SqlAlchemyLotRepository,
    SqlAlchemyMaterialRepository,
)
from aurum.modules.inventory.presentation.schemas import LotResponse, MaterialResponse
from aurum.modules.publicapi.application.dto import ApiKeyContext
from aurum.modules.publicapi.presentation.dependencies import public_session
from aurum.modules.purchasing.infrastructure.repositories import (
    SqlAlchemyPurchaseOrderRepository,
)
from aurum.modules.quality.infrastructure.repositories import (
    SqlAlchemyQualitySampleRepository,
)
from aurum.modules.reports.application.services import ReportsService
from aurum.modules.reports.presentation.schemas import ReportTableResponse
from aurum.modules.sales.infrastructure.repositories import SqlAlchemySalesOrderRepository
from aurum.modules.transformation.infrastructure.repositories import (
    SqlAlchemyTransformationOrderRepository,
)

router = APIRouter(prefix="/public/v1", tags=["public-api"])

_InventoryCtx = Annotated[
    tuple[AsyncSession, ApiKeyContext], Depends(public_session("inventory:read"))
]
_ReportsCtx = Annotated[
    tuple[AsyncSession, ApiKeyContext], Depends(public_session("reports:read"))
]


@router.get("/inventory/materials", response_model=list[MaterialResponse])
async def public_materials(ctx: _InventoryCtx) -> list[MaterialResponse]:
    session, key = ctx
    service = InventoryService(
        tenant_id=key.tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
    )
    return [MaterialResponse.from_view(v) for v in await service.list_materials()]


@router.get("/inventory/lots", response_model=list[LotResponse])
async def public_lots(ctx: _InventoryCtx) -> list[LotResponse]:
    session, key = ctx
    service = InventoryService(
        tenant_id=key.tenant_id,
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
    )
    return [LotResponse.from_view(v) for v in await service.list_lots()]


@router.get("/reports/{report_key}", response_model=ReportTableResponse)
async def public_report(report_key: str, ctx: _ReportsCtx) -> ReportTableResponse:
    session, key = ctx
    service = ReportsService(
        lots=SqlAlchemyLotRepository(session),
        materials=SqlAlchemyMaterialRepository(session),
        sales=SqlAlchemySalesOrderRepository(session),
        purchases=SqlAlchemyPurchaseOrderRepository(session),
        transformations=SqlAlchemyTransformationOrderRepository(session),
        samples=SqlAlchemyQualitySampleRepository(session),
        accounting=build_accounting_service(session, key.tenant_id),
        branding=SqlAlchemyBrandingRepository(session),
        parameters=SqlAlchemyParametersRepository(session),
        spot_provider=get_spot_prices,
    )
    return ReportTableResponse.from_view(await service.generate(report_key))
