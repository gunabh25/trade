"""Enterprise analytics API schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsMetricsResponse(BaseModel):
    total_trades: int
    total_pnl: Decimal
    win_count: int
    loss_count: int
    breakeven_count: int
    win_rate: float
    loss_rate: float
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: float | None
    expectancy: float
    average_r: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown_pct: float
    max_drawdown_dollars: Decimal
    recovery_factor: float | None
    max_consecutive_wins: int
    max_consecutive_losses: int
    starting_equity: Decimal
    ending_equity: Decimal


class EquityPointResponse(BaseModel):
    date: date
    equity: Decimal


class ProfitCurvePointResponse(BaseModel):
    trade_index: int
    cumulative_pnl: Decimal


class DrawdownPointResponse(BaseModel):
    date: date
    drawdown_pct: float


class ReturnPointResponse(BaseModel):
    label: str
    value: Decimal


class CalendarHeatmapDayResponse(BaseModel):
    date: date
    pnl: Decimal
    trade_count: int


class HourHeatmapCellResponse(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday … 6=Sunday")
    hour: int = Field(ge=0, le=23)
    pnl: Decimal
    trade_count: int


class DistributionBucketResponse(BaseModel):
    label: str
    count: int


class PieSliceResponse(BaseModel):
    name: str
    value: float
    color: str | None = None


class SymbolPerformanceResponse(BaseModel):
    symbol: str
    trade_count: int
    total_pnl: Decimal
    win_rate: float
    avg_pnl: Decimal


class SessionPerformanceResponse(BaseModel):
    session: str
    trade_count: int
    total_pnl: Decimal
    win_rate: float


class LeaderboardEntryResponse(BaseModel):
    rank: int
    id: str
    name: str
    subtitle: str | None = None
    pnl: Decimal
    win_rate: float
    profit_factor: float | None
    trade_count: int
    sharpe_ratio: float | None = None


class ComparisonSeriesResponse(BaseModel):
    id: str
    name: str
    color: str
    points: list[EquityPointResponse]


class AnalyticsOverviewResponse(BaseModel):
    metrics: AnalyticsMetricsResponse
    equity_curve: list[EquityPointResponse]
    profit_curve: list[ProfitCurvePointResponse]
    drawdown: list[DrawdownPointResponse]
    daily_returns: list[ReturnPointResponse]
    monthly_returns: list[ReturnPointResponse]
    calendar_heatmap: list[CalendarHeatmapDayResponse]
    hour_heatmap: list[HourHeatmapCellResponse]
    trade_distribution: list[DistributionBucketResponse]
    win_loss_pie: list[PieSliceResponse]
    symbol_pie: list[PieSliceResponse]
    strategy_pie: list[PieSliceResponse]
    symbol_performance: list[SymbolPerformanceResponse]
    session_performance: list[SessionPerformanceResponse]
    account_leaderboard: list[LeaderboardEntryResponse]
    strategy_leaderboard: list[LeaderboardEntryResponse]
    comparison: list[ComparisonSeriesResponse]
    strategy_comparison: list[ComparisonSeriesResponse]


class AnalyticsFilterParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    trading_account_id: UUID | None = None
    strategy_id: UUID | None = None
