"""Trading journal API routes."""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.db.enums import JournalSource
from tradeflow.features.journal.schemas import (
    AddScreenshotRequest,
    CalendarDayResponse,
    CreateJournalEntryRequest,
    CreateStrategyRequest,
    EmotionStatsResponse,
    ImportTradesRequest,
    ImportTradesResponse,
    JournalEntryResponse,
    JournalFilterParams,
    JournalStatsResponse,
    ScreenshotResponse,
    StrategyPerformanceResponse,
    StrategyResponse,
    UpdateJournalEntryRequest,
    UpdateStrategyRequest,
)
from tradeflow.features.journal.service import JournalService

router = APIRouter(prefix="/journal", tags=["Trading Journal"])


@router.get(
    "/entries",
    response_model=SuccessResponse[dict[str, object]],
    summary="List journal entries with search and filters",
)
@inject
async def list_entries(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    q: str | None = None,
    strategy_id: UUID | None = None,
    symbol: str | None = None,
    tag: str | None = None,
    emotion: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    source: JournalSource | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[dict[str, object]]:
    from datetime import date as date_type

    filters = JournalFilterParams(
        q=q,
        strategy_id=strategy_id,
        symbol=symbol,
        tag=tag,
        emotion=emotion,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        source=source,
        page=page,
        page_size=page_size,
    )
    entries, total = await journal_service.list_entries(db, user.id, filters)
    return success(
        {
            "entries": entries,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/entries",
    response_model=SuccessResponse[JournalEntryResponse],
    summary="Create journal entry",
)
@inject
async def create_entry(
    request: Request,
    payload: CreateJournalEntryRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[JournalEntryResponse]:
    entry = await journal_service.create_entry(db, user.id, payload)
    return success(entry, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/entries/{entry_id}",
    response_model=SuccessResponse[JournalEntryResponse],
    summary="Get journal entry",
)
@inject
async def get_entry(
    request: Request,
    entry_id: UUID,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[JournalEntryResponse]:
    entry = await journal_service.get_entry(db, user.id, entry_id)
    return success(entry, request_id=getattr(request.state, "request_id", None))


@router.put(
    "/entries/{entry_id}",
    response_model=SuccessResponse[JournalEntryResponse],
    summary="Update journal entry",
)
@inject
async def update_entry(
    request: Request,
    entry_id: UUID,
    payload: UpdateJournalEntryRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[JournalEntryResponse]:
    entry = await journal_service.update_entry(db, user.id, entry_id, payload)
    return success(entry, request_id=getattr(request.state, "request_id", None))


@router.delete(
    "/entries/{entry_id}",
    response_model=SuccessResponse[dict[str, str]],
    summary="Delete journal entry",
)
@inject
async def delete_entry(
    request: Request,
    entry_id: UUID,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[dict[str, str]]:
    await journal_service.delete_entry(db, user.id, entry_id)
    return success({"status": "deleted"}, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/entries/{entry_id}/screenshots",
    response_model=SuccessResponse[ScreenshotResponse],
    summary="Add screenshot to journal entry",
)
@inject
async def add_screenshot(
    request: Request,
    entry_id: UUID,
    payload: AddScreenshotRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[ScreenshotResponse]:
    screenshot = await journal_service.add_screenshot(db, user.id, entry_id, payload)
    return success(screenshot, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/import",
    response_model=SuccessResponse[ImportTradesResponse],
    summary="Auto-import closed trades into journal",
)
@inject
async def import_trades(
    request: Request,
    payload: ImportTradesRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[ImportTradesResponse]:
    result = await journal_service.import_trades(db, user.id, payload)
    return success(result, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/calendar",
    response_model=SuccessResponse[list[CalendarDayResponse]],
    summary="Calendar view — daily PnL aggregation",
)
@inject
async def get_calendar(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    year: int = Query(ge=2020, le=2100),
    month: int = Query(ge=1, le=12),
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[list[CalendarDayResponse]]:
    days = await journal_service.get_calendar(db, user.id, year=year, month=month)
    return success(days, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/stats",
    response_model=SuccessResponse[JournalStatsResponse],
    summary="Journal statistics",
)
@inject
async def get_stats(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    date_from: str | None = None,
    date_to: str | None = None,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[JournalStatsResponse]:
    from datetime import date as date_type

    stats = await journal_service.get_stats(
        db,
        user.id,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
    )
    return success(stats, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/stats/by-strategy",
    response_model=SuccessResponse[list[StrategyPerformanceResponse]],
    summary="Performance breakdown by strategy",
)
@inject
async def get_strategy_performance(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[list[StrategyPerformanceResponse]]:
    data = await journal_service.get_strategy_performance(db, user.id)
    return success(data, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/stats/emotions",
    response_model=SuccessResponse[list[EmotionStatsResponse]],
    summary="Performance by emotion",
)
@inject
async def get_emotion_stats(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[list[EmotionStatsResponse]]:
    data = await journal_service.get_emotion_stats(db, user.id)
    return success(data, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/tags",
    response_model=SuccessResponse[list[str]],
    summary="List all tags",
)
@inject
async def list_tags(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[list[str]]:
    tags = await journal_service.list_tags(db, user.id)
    return success(tags, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/strategies",
    response_model=SuccessResponse[list[StrategyResponse]],
    summary="List strategies",
)
@inject
async def list_strategies(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[list[StrategyResponse]]:
    strategies = await journal_service.list_strategies(db, user.id)
    return success(strategies, request_id=getattr(request.state, "request_id", None))


@router.post(
    "/strategies",
    response_model=SuccessResponse[StrategyResponse],
    summary="Create strategy",
)
@inject
async def create_strategy(
    request: Request,
    payload: CreateStrategyRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[StrategyResponse]:
    strategy = await journal_service.create_strategy(db, user.id, payload)
    return success(strategy, request_id=getattr(request.state, "request_id", None))


@router.put(
    "/strategies/{strategy_id}",
    response_model=SuccessResponse[StrategyResponse],
    summary="Update strategy",
)
@inject
async def update_strategy(
    request: Request,
    strategy_id: UUID,
    payload: UpdateStrategyRequest,
    db: DbSession,
    user: CurrentUser,
    journal_service: JournalService = Depends(Provide[Container.journal_service]),
) -> SuccessResponse[StrategyResponse]:
    strategy = await journal_service.update_strategy(db, user.id, strategy_id, payload)
    return success(strategy, request_id=getattr(request.state, "request_id", None))
