"""Trading journal API schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from tradeflow.db.enums import JournalSource, TradeEmotion, TradeSide


class StrategyResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    symbols: list[str] | None
    color: str | None
    rules: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateStrategyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    symbols: list[str] | None = None
    color: str | None = Field(default="#22c55e", pattern=r"^#[0-9A-Fa-f]{6}$")
    rules: str | None = None


class UpdateStrategyRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    symbols: list[str] | None = None
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    rules: str | None = None
    is_active: bool | None = None


class ScreenshotResponse(BaseModel):
    id: UUID
    file_url: str
    caption: str | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalEntryResponse(BaseModel):
    id: UUID
    title: str
    content: str | None
    notes: str | None
    mood: str | None
    session_date: date
    pnl: Decimal | None
    tags: list[str] | None
    emotions: list[str] | None
    mistakes: list[str] | None
    lessons_learned: str | None
    source: JournalSource
    symbol: str | None
    side: TradeSide | None
    quantity: int | None
    entry_price: Decimal | None
    exit_price: Decimal | None
    grade: int | None = None
    trade_id: UUID | None
    strategy_id: UUID | None
    trading_account_id: UUID | None
    strategy: StrategyResponse | None = None
    screenshots: list[ScreenshotResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateJournalEntryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    session_date: date
    content: str | None = None
    notes: str | None = None
    mood: str | None = None
    pnl: Decimal | None = None
    tags: list[str] | None = None
    emotions: list[TradeEmotion | str] | None = None
    mistakes: list[str] | None = None
    lessons_learned: str | None = None
    symbol: str | None = None
    side: TradeSide | None = None
    quantity: int | None = Field(default=None, ge=1)
    entry_price: Decimal | None = None
    exit_price: Decimal | None = None
    grade: int | None = Field(default=None, ge=1, le=5)
    trade_id: UUID | None = None
    strategy_id: UUID | None = None
    trading_account_id: UUID | None = None


class UpdateJournalEntryRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    session_date: date | None = None
    content: str | None = None
    notes: str | None = None
    mood: str | None = None
    pnl: Decimal | None = None
    tags: list[str] | None = None
    emotions: list[TradeEmotion | str] | None = None
    mistakes: list[str] | None = None
    lessons_learned: str | None = None
    symbol: str | None = None
    side: TradeSide | None = None
    quantity: int | None = Field(default=None, ge=1)
    entry_price: Decimal | None = None
    exit_price: Decimal | None = None
    grade: int | None = Field(default=None, ge=1, le=5)
    strategy_id: UUID | None = None


class AddScreenshotRequest(BaseModel):
    file_url: str = Field(min_length=1, max_length=500)
    caption: str | None = Field(default=None, max_length=255)


class ImportTradesRequest(BaseModel):
    trading_account_id: UUID | None = None
    since: date | None = None


class ImportTradesResponse(BaseModel):
    imported: int
    skipped: int


class JournalFilterParams(BaseModel):
    q: str | None = None
    strategy_id: UUID | None = None
    symbol: str | None = None
    tag: str | None = None
    emotion: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    source: JournalSource | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CalendarDayResponse(BaseModel):
    date: date
    pnl: Decimal
    trade_count: int


class JournalStatsResponse(BaseModel):
    total_entries: int
    total_pnl: Decimal
    win_count: int
    loss_count: int
    breakeven_count: int
    win_rate: float
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: float | None
    best_trade: Decimal | None
    worst_trade: Decimal | None
    avg_rr: float | None


class StrategyPerformanceResponse(BaseModel):
    strategy_id: UUID | None
    strategy_name: str
    color: str | None
    trade_count: int
    total_pnl: Decimal
    win_rate: float
    avg_pnl: Decimal


class EmotionStatsResponse(BaseModel):
    emotion: str
    count: int
    total_pnl: Decimal
    win_rate: float


class WeekdayPerformanceResponse(BaseModel):
    weekday: str
    weekday_index: int
    trade_count: int
    total_pnl: Decimal
    win_rate: float


class SymbolPerformanceResponse(BaseModel):
    symbol: str
    trade_count: int
    total_pnl: Decimal
    win_rate: float
    avg_pnl: Decimal


class MistakeStatsResponse(BaseModel):
    mistake: str
    count: int
    total_pnl: Decimal
