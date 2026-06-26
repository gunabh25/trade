"""Enterprise analytics API routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.analytics.schemas import AnalyticsFilterParams, AnalyticsOverviewResponse
from tradeflow.features.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _build_filters(
    *,
    date_from: date | None,
    date_to: date | None,
    trading_account_id: UUID | None,
    strategy_id: UUID | None,
) -> AnalyticsFilterParams:
    return AnalyticsFilterParams(
        date_from=date_from,
        date_to=date_to,
        trading_account_id=trading_account_id,
        strategy_id=strategy_id,
    )


@router.get(
    "/overview",
    response_model=SuccessResponse[AnalyticsOverviewResponse],
    summary="Full analytics dashboard payload",
)
@inject
async def get_analytics_overview(
    db: DbSession,
    user: CurrentUser,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    trading_account_id: UUID | None = Query(default=None),
    strategy_id: UUID | None = Query(default=None),
    service: AnalyticsService = Depends(Provide[Container.analytics_service]),
) -> SuccessResponse[AnalyticsOverviewResponse]:
    filters = _build_filters(
        date_from=date_from,
        date_to=date_to,
        trading_account_id=trading_account_id,
        strategy_id=strategy_id,
    )
    overview = await service.get_overview(db, user.id, filters)
    return success(overview)


@router.get(
    "/export/csv",
    summary="Export analytics report as CSV",
)
@inject
async def export_analytics_csv(
    db: DbSession,
    user: CurrentUser,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    trading_account_id: UUID | None = Query(default=None),
    strategy_id: UUID | None = Query(default=None),
    service: AnalyticsService = Depends(Provide[Container.analytics_service]),
) -> Response:
    filters = _build_filters(
        date_from=date_from,
        date_to=date_to,
        trading_account_id=trading_account_id,
        strategy_id=strategy_id,
    )
    data = await service.export_csv(db, user.id, filters)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="analytics-report.csv"'},
    )


@router.get(
    "/export/pdf",
    summary="Export analytics report as PDF",
)
@inject
async def export_analytics_pdf(
    db: DbSession,
    user: CurrentUser,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    trading_account_id: UUID | None = Query(default=None),
    strategy_id: UUID | None = Query(default=None),
    service: AnalyticsService = Depends(Provide[Container.analytics_service]),
) -> Response:
    filters = _build_filters(
        date_from=date_from,
        date_to=date_to,
        trading_account_id=trading_account_id,
        strategy_id=strategy_id,
    )
    data = await service.export_pdf(db, user.id, filters)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="analytics-report.pdf"'},
    )
