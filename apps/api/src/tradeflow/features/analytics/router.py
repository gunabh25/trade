"""Enterprise analytics API routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.features.analytics.schemas import AnalyticsFilterParams, AnalyticsOverviewResponse
from tradeflow.features.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


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
    filters = AnalyticsFilterParams(
        date_from=date_from,
        date_to=date_to,
        trading_account_id=trading_account_id,
        strategy_id=strategy_id,
    )
    overview = await service.get_overview(db, user.id, filters)
    return success(overview)
