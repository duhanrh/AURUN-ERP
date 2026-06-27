"""Endpoints de Contabilidad y Tesorería (``/accounting``), sección 7.12/7.13.

Lectura (plan, libro mayor, balance, cartera): ``accounting:access``. Asiento
manual: ``accounting:manual_entry``. Registro de pagos (tesorería): ``treasury:manage``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aurum.modules.accounting.application.services import AccountingService
from aurum.modules.accounting.infrastructure.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyJournalEntryRepository,
)
from aurum.modules.accounting.presentation.schemas import (
    AccountingKpisResponse,
    AccountResponse,
    BalanceSheetResponse,
    CreateManualEntryRequest,
    JournalEntryResponse,
    PartyBalanceResponse,
    RegisterPaymentRequest,
)
from aurum.modules.audit.domain.actions import ACCOUNTING_MANUAL_ENTRY
from aurum.modules.audit.presentation.recorder import record_event
from aurum.modules.auth.presentation.dependencies import Principal, require_permission
from aurum.shared.dependencies import get_session, require_tenant_id

router = APIRouter(prefix="/accounting", tags=["accounting"])

_read = Depends(require_permission("accounting:access"))
_manual = Depends(require_permission("accounting:manual_entry"))
_treasury = Depends(require_permission("treasury:manage"))


def build_accounting_service(
    session: AsyncSession, tenant_id: uuid.UUID
) -> AccountingService:
    """Factory reutilizado por Compras y Ventas para postear asientos automáticos."""
    return AccountingService(
        tenant_id=tenant_id,
        accounts=SqlAlchemyAccountRepository(session),
        journals=SqlAlchemyJournalEntryRepository(session),
    )


@router.get("/accounts", response_model=list[AccountResponse], dependencies=[_read])
async def list_accounts(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[AccountResponse]:
    views = await build_accounting_service(session, tenant_id).list_accounts()
    return [AccountResponse.from_view(v) for v in views]


@router.get("/journal", response_model=list[JournalEntryResponse], dependencies=[_read])
async def list_journal(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[JournalEntryResponse]:
    views = await build_accounting_service(session, tenant_id).list_entries()
    return [JournalEntryResponse.from_view(v) for v in views]


@router.get("/kpis", response_model=AccountingKpisResponse, dependencies=[_read])
async def accounting_kpis(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> AccountingKpisResponse:
    return AccountingKpisResponse.from_view(
        await build_accounting_service(session, tenant_id).kpis()
    )


@router.get("/balance-sheet", response_model=BalanceSheetResponse, dependencies=[_read])
async def balance_sheet(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> BalanceSheetResponse:
    return BalanceSheetResponse.from_view(
        await build_accounting_service(session, tenant_id).balance_sheet()
    )


@router.get("/receivables", response_model=list[PartyBalanceResponse], dependencies=[_read])
async def receivables(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[PartyBalanceResponse]:
    views = await build_accounting_service(session, tenant_id).receivables()
    return [PartyBalanceResponse.from_view(v) for v in views]


@router.get("/payables", response_model=list[PartyBalanceResponse], dependencies=[_read])
async def payables(
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> list[PartyBalanceResponse]:
    views = await build_accounting_service(session, tenant_id).payables()
    return [PartyBalanceResponse.from_view(v) for v in views]


@router.post(
    "/journal",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_entry(
    payload: CreateManualEntryRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    principal: Principal = _manual,
) -> JournalEntryResponse:
    view = await build_accounting_service(session, tenant_id).create_manual_entry(
        payload.to_dto()
    )
    await record_event(
        session, tenant_id, action=ACCOUNTING_MANUAL_ENTRY, entity_type="journal_entry",
        entity_id=view.id, principal=principal, request=request,
        changes={"entry_code": view.entry_code, "memo": view.memo},
    )
    return JournalEntryResponse.from_view(view)


@router.post(
    "/payments",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_treasury],
)
async def register_payment(
    payload: RegisterPaymentRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
) -> JournalEntryResponse:
    view = await build_accounting_service(session, tenant_id).register_payment(
        payload.to_dto()
    )
    return JournalEntryResponse.from_view(view)
