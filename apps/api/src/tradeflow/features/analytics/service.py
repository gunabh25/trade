"""Enterprise analytics business logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.db.enums import TradeStatus
from tradeflow.db.models.journal import Strategy, TradeJournal
from tradeflow.db.models.trading import Trade, TradingAccount
from tradeflow.features.analytics import metrics
from tradeflow.features.analytics.export import export_overview_csv, export_overview_pdf
from tradeflow.features.analytics.schemas import (
    AnalyticsFilterParams,
    AnalyticsMetricsResponse,
    AnalyticsOverviewResponse,
    CalendarHeatmapDayResponse,
    ComparisonSeriesResponse,
    DistributionBucketResponse,
    DrawdownPointResponse,
    EquityPointResponse,
    HourHeatmapCellResponse,
    LeaderboardEntryResponse,
    PieSliceResponse,
    ProfitCurvePointResponse,
    ReturnPointResponse,
    SessionPerformanceResponse,
    SymbolPerformanceResponse,
)

DEFAULT_STARTING_EQUITY = Decimal("100000")
PIE_COLORS = [
    "#22c55e",
    "#3b82f6",
    "#a855f7",
    "#f59e0b",
    "#ef4444",
    "#06b6d4",
    "#ec4899",
    "#64748b",
]
COMPARISON_COLORS = ["#22c55e", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444"]

SESSION_HOURS: dict[str, range] = {
    "Asia": range(0, 8),
    "London": range(8, 13),
    "New York": range(13, 21),
    "After Hours": range(21, 24),
}


class AnalyticsService:
    """Compute portfolio-level and comparative trading analytics."""

    async def get_overview(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams | None = None,
    ) -> AnalyticsOverviewResponse:
        filters = filters or AnalyticsFilterParams()
        trades = await self._load_closed_trades(db, user_id, filters)
        journal_entries = await self._load_journal_entries(db, user_id, filters)

        pnls = self._collect_pnls(trades, journal_entries)
        ordered_pnls = self._collect_ordered_pnls(trades, journal_entries)
        trade_dates = self._collect_trade_dates(trades, journal_entries)

        starting_equity = DEFAULT_STARTING_EQUITY
        daily = metrics.aggregate_daily_pnls(trade_dates)
        equity_series = metrics.equity_curve_from_daily(daily, starting_equity)
        if not equity_series:
            equity_series = [(date.today(), float(starting_equity))]
        drawdown_series = metrics.drawdown_series(equity_series)
        daily_rates = metrics.daily_return_rates(daily, starting_equity)
        trade_metrics = metrics.compute_trade_metrics(ordered_pnls)

        ending_equity = Decimal(str(equity_series[-1][1])) if equity_series else starting_equity
        max_dd = min((dd for _, dd in drawdown_series), default=0.0)
        max_dd_dollars = Decimal(str(abs(metrics.max_drawdown_dollars(equity_series))))
        net_profit = float(trade_metrics["total_pnl"])
        recovery = metrics.recovery_factor(net_profit, float(max_dd_dollars))

        metrics_response = AnalyticsMetricsResponse(
            total_trades=len(pnls),
            total_pnl=Decimal(str(trade_metrics["total_pnl"])),
            win_count=int(trade_metrics["win_count"]),
            loss_count=int(trade_metrics["loss_count"]),
            breakeven_count=int(trade_metrics["breakeven_count"]),
            win_rate=float(trade_metrics["win_rate"]),
            loss_rate=float(trade_metrics["loss_rate"]),
            avg_win=Decimal(str(trade_metrics["avg_win"])),
            avg_loss=Decimal(str(trade_metrics["avg_loss"])),
            profit_factor=trade_metrics["profit_factor"],
            expectancy=float(trade_metrics["expectancy"]),
            average_r=trade_metrics["average_r"],
            sharpe_ratio=metrics.sharpe_ratio(daily_rates),
            sortino_ratio=metrics.sortino_ratio(daily_rates),
            max_drawdown_pct=max_dd,
            max_drawdown_dollars=max_dd_dollars,
            recovery_factor=recovery,
            max_consecutive_wins=int(trade_metrics["max_consecutive_wins"]),
            max_consecutive_losses=int(trade_metrics["max_consecutive_losses"]),
            starting_equity=starting_equity,
            ending_equity=ending_equity,
        )

        profit_curve = metrics.profit_curve_from_trades(trade_dates)
        distribution = metrics.trade_distribution(ordered_pnls)

        return AnalyticsOverviewResponse(
            metrics=metrics_response,
            equity_curve=[
                EquityPointResponse(date=d, equity=Decimal(str(eq))) for d, eq in equity_series
            ],
            profit_curve=[
                ProfitCurvePointResponse(
                    trade_index=idx,
                    cumulative_pnl=Decimal(str(cum)),
                )
                for idx, cum in profit_curve
            ],
            drawdown=[DrawdownPointResponse(date=d, drawdown_pct=dd) for d, dd in drawdown_series],
            daily_returns=self._daily_return_points(daily),
            monthly_returns=self._monthly_return_points(daily),
            calendar_heatmap=self._calendar_heatmap(trades, journal_entries),
            hour_heatmap=self._hour_heatmap(trades),
            trade_distribution=[
                DistributionBucketResponse(label=label, count=count)
                for label, count in distribution
            ],
            win_loss_pie=self._win_loss_pie(pnls),
            symbol_pie=self._symbol_pie(trades, journal_entries),
            strategy_pie=await self._strategy_pie(db, user_id, trades, journal_entries),
            symbol_performance=self._symbol_performance(trades, journal_entries),
            session_performance=self._session_performance(trades),
            account_leaderboard=await self._account_leaderboard(db, user_id, filters),
            strategy_leaderboard=await self._strategy_leaderboard(db, user_id, filters),
            comparison=await self._comparison_series(db, user_id, filters),
            strategy_comparison=await self._strategy_comparison_series(db, user_id, filters),
        )

    async def export_csv(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams | None = None,
    ) -> bytes:
        overview = await self.get_overview(db, user_id, filters)
        return export_overview_csv(overview)

    async def export_pdf(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams | None = None,
    ) -> bytes:
        overview = await self.get_overview(db, user_id, filters)
        return export_overview_pdf(overview)

    async def _load_closed_trades(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[Trade]:
        query = (
            select(Trade)
            .options(selectinload(Trade.strategy), selectinload(Trade.trading_account))
            .where(
                Trade.user_id == user_id,
                Trade.deleted_at.is_(None),
                Trade.status == TradeStatus.CLOSED,
                Trade.realized_pnl.isnot(None),
            )
        )
        if filters.trading_account_id:
            query = query.where(Trade.trading_account_id == filters.trading_account_id)
        if filters.strategy_id:
            query = query.where(Trade.strategy_id == filters.strategy_id)
        if filters.date_from:
            query = query.where(func.date(Trade.closed_at) >= filters.date_from)
        if filters.date_to:
            query = query.where(func.date(Trade.closed_at) <= filters.date_to)

        return list((await db.scalars(query.order_by(Trade.closed_at))).all())

    async def _load_journal_entries(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[TradeJournal]:
        query = (
            select(TradeJournal)
            .options(selectinload(TradeJournal.strategy))
            .where(
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
                TradeJournal.pnl.isnot(None),
                TradeJournal.trade_id.is_(None),
            )
        )
        if filters.trading_account_id:
            query = query.where(TradeJournal.trading_account_id == filters.trading_account_id)
        if filters.strategy_id:
            query = query.where(TradeJournal.strategy_id == filters.strategy_id)
        if filters.date_from:
            query = query.where(TradeJournal.session_date >= filters.date_from)
        if filters.date_to:
            query = query.where(TradeJournal.session_date <= filters.date_to)

        return list((await db.scalars(query)).all())

    def _collect_pnls(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[Decimal]:
        pnls = [t.realized_pnl for t in trades if t.realized_pnl is not None]
        pnls.extend(e.pnl for e in journal_entries if e.pnl is not None)
        return pnls

    def _collect_ordered_pnls(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[Decimal]:
        from datetime import datetime

        items: list[tuple[datetime | date, Decimal]] = []
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            ts = trade.closed_at or trade.opened_at
            items.append((ts, trade.realized_pnl))
        for entry in journal_entries:
            if entry.pnl is None:
                continue
            items.append((entry.session_date, entry.pnl))
        items.sort(key=lambda x: x[0])
        return [pnl for _, pnl in items]

    def _collect_trade_dates(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[tuple[date, Decimal]]:
        points: list[tuple[date, Decimal]] = []
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            day = trade.closed_at.date() if trade.closed_at else trade.opened_at.date()
            points.append((day, trade.realized_pnl))
        for entry in journal_entries:
            if entry.pnl is None:
                continue
            points.append((entry.session_date, entry.pnl))
        return points

    def _daily_return_points(
        self,
        daily: list[tuple[date, Decimal]],
        limit: int = 90,
    ) -> list[ReturnPointResponse]:
        recent = daily[-limit:]
        return [ReturnPointResponse(label=d.strftime("%a %m/%d"), value=pnl) for d, pnl in recent]

    def _monthly_return_points(
        self,
        daily: list[tuple[date, Decimal]],
    ) -> list[ReturnPointResponse]:
        monthly = metrics.monthly_returns(daily)
        return [
            ReturnPointResponse(
                label=month,
                value=Decimal(str(value)),
            )
            for month, value in monthly[-12:]
        ]

    def _calendar_heatmap(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[CalendarHeatmapDayResponse]:
        buckets: dict[date, tuple[Decimal, int]] = defaultdict(
            lambda: (Decimal("0"), 0),
        )
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            day = trade.closed_at.date() if trade.closed_at else trade.opened_at.date()
            pnl, count = buckets[day]
            buckets[day] = (pnl + trade.realized_pnl, count + 1)
        for entry in journal_entries:
            if entry.pnl is None:
                continue
            pnl, count = buckets[entry.session_date]
            buckets[entry.session_date] = (pnl + entry.pnl, count + 1)

        return [
            CalendarHeatmapDayResponse(date=day, pnl=pnl, trade_count=count)
            for day, (pnl, count) in sorted(buckets.items())
        ]

    def _hour_heatmap(self, trades: list[Trade]) -> list[HourHeatmapCellResponse]:
        buckets: dict[tuple[int, int], tuple[Decimal, int]] = defaultdict(
            lambda: (Decimal("0"), 0),
        )
        for trade in trades:
            if trade.realized_pnl is None or trade.closed_at is None:
                continue
            dow = trade.closed_at.weekday()
            hour = trade.closed_at.hour
            pnl, count = buckets[(dow, hour)]
            buckets[(dow, hour)] = (pnl + trade.realized_pnl, count + 1)

        return [
            HourHeatmapCellResponse(
                day_of_week=dow,
                hour=hour,
                pnl=pnl,
                trade_count=count,
            )
            for (dow, hour), (pnl, count) in sorted(buckets.items())
        ]

    def _win_loss_pie(self, pnls: list[Decimal]) -> list[PieSliceResponse]:
        wins = sum(float(p) for p in pnls if p > 0)
        losses = abs(sum(float(p) for p in pnls if p < 0))
        if wins == 0 and losses == 0:
            return []
        return [
            PieSliceResponse(name="Wins", value=wins, color="#22c55e"),
            PieSliceResponse(name="Losses", value=losses, color="#ef4444"),
        ]

    def _symbol_pie(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[PieSliceResponse]:
        buckets: dict[str, float] = defaultdict(float)
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            buckets[trade.symbol] += abs(float(trade.realized_pnl))
        for entry in journal_entries:
            if entry.pnl is None or not entry.symbol:
                continue
            buckets[entry.symbol] += abs(float(entry.pnl))

        sorted_items = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:8]
        return [
            PieSliceResponse(name=name, value=value, color=PIE_COLORS[i % len(PIE_COLORS)])
            for i, (name, value) in enumerate(sorted_items)
        ]

    async def _strategy_pie(
        self,
        db: AsyncSession,
        user_id: UUID,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[PieSliceResponse]:
        strategies = {
            s.id: s
            for s in (
                await db.scalars(
                    select(Strategy).where(
                        Strategy.user_id == user_id,
                        Strategy.deleted_at.is_(None),
                    ),
                )
            ).all()
        }

        buckets: dict[str, float] = defaultdict(float)
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            if trade.strategy_id in strategies:
                name = strategies[trade.strategy_id].name
            else:
                name = "Unassigned"
            buckets[name] += abs(float(trade.realized_pnl))
        for entry in journal_entries:
            if entry.pnl is None:
                continue
            name = entry.strategy.name if entry.strategy else "Unassigned"
            buckets[name] += abs(float(entry.pnl))

        name_to_color = {s.name: s.color for s in strategies.values() if s.color}
        sorted_items = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:8]
        return [
            PieSliceResponse(
                name=name,
                value=value,
                color=name_to_color.get(name) or PIE_COLORS[i % len(PIE_COLORS)],
            )
            for i, (name, value) in enumerate(sorted_items)
        ]

    async def _account_leaderboard(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[LeaderboardEntryResponse]:
        accounts = list(
            (
                await db.scalars(
                    select(TradingAccount).where(
                        TradingAccount.user_id == user_id,
                        TradingAccount.deleted_at.is_(None),
                    ),
                )
            ).all(),
        )
        entries: list[LeaderboardEntryResponse] = []

        for account in accounts:
            account_filters = AnalyticsFilterParams(
                date_from=filters.date_from,
                date_to=filters.date_to,
                trading_account_id=account.id,
                strategy_id=filters.strategy_id,
            )
            trades = await self._load_closed_trades(db, user_id, account_filters)
            pnls = [t.realized_pnl for t in trades if t.realized_pnl is not None]
            if not pnls:
                continue

            trade_metrics = metrics.compute_trade_metrics(pnls)
            daily = metrics.aggregate_daily_pnls(
                [
                    (
                        t.closed_at.date() if t.closed_at else t.opened_at.date(),
                        t.realized_pnl,
                    )
                    for t in trades
                    if t.realized_pnl is not None
                ],
            )
            rates = metrics.daily_return_rates(daily, DEFAULT_STARTING_EQUITY)

            entries.append(
                LeaderboardEntryResponse(
                    rank=0,
                    id=str(account.id),
                    name=account.name,
                    subtitle=account.account_role,
                    pnl=Decimal(str(trade_metrics["total_pnl"])),
                    win_rate=float(trade_metrics["win_rate"]),
                    profit_factor=trade_metrics["profit_factor"],
                    trade_count=len(pnls),
                    sharpe_ratio=metrics.sharpe_ratio(rates),
                ),
            )

        entries.sort(key=lambda e: float(e.pnl), reverse=True)
        for i, entry in enumerate(entries, start=1):
            entries[i - 1] = entry.model_copy(update={"rank": i})
        return entries[:10]

    async def _strategy_leaderboard(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[LeaderboardEntryResponse]:
        strategies = list(
            (
                await db.scalars(
                    select(Strategy).where(
                        Strategy.user_id == user_id,
                        Strategy.deleted_at.is_(None),
                    ),
                )
            ).all(),
        )
        entries: list[LeaderboardEntryResponse] = []

        for strategy in strategies:
            strategy_filters = AnalyticsFilterParams(
                date_from=filters.date_from,
                date_to=filters.date_to,
                trading_account_id=filters.trading_account_id,
                strategy_id=strategy.id,
            )
            trades = await self._load_closed_trades(db, user_id, strategy_filters)
            journal_entries = await self._load_journal_entries(db, user_id, strategy_filters)
            pnls = self._collect_pnls(trades, journal_entries)
            if not pnls:
                continue

            trade_metrics = metrics.compute_trade_metrics(pnls)
            entries.append(
                LeaderboardEntryResponse(
                    rank=0,
                    id=str(strategy.id),
                    name=strategy.name,
                    subtitle=str(len(strategy.symbols or [])) + " symbols"
                    if strategy.symbols
                    else None,
                    pnl=Decimal(str(trade_metrics["total_pnl"])),
                    win_rate=float(trade_metrics["win_rate"]),
                    profit_factor=trade_metrics["profit_factor"],
                    trade_count=len(pnls),
                ),
            )

        entries.sort(key=lambda e: float(e.pnl), reverse=True)
        for i, entry in enumerate(entries, start=1):
            entries[i - 1] = entry.model_copy(update={"rank": i})
        return entries[:10]

    async def _comparison_series(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[ComparisonSeriesResponse]:
        accounts = list(
            (
                await db.scalars(
                    select(TradingAccount)
                    .where(
                        TradingAccount.user_id == user_id,
                        TradingAccount.deleted_at.is_(None),
                    )
                    .order_by(TradingAccount.created_at)
                    .limit(5),
                )
            ).all(),
        )

        series_list: list[ComparisonSeriesResponse] = []
        for i, account in enumerate(accounts):
            account_filters = AnalyticsFilterParams(
                date_from=filters.date_from,
                date_to=filters.date_to,
                trading_account_id=account.id,
            )
            trades = await self._load_closed_trades(db, user_id, account_filters)
            daily = metrics.aggregate_daily_pnls(
                [
                    (
                        t.closed_at.date() if t.closed_at else t.opened_at.date(),
                        t.realized_pnl,
                    )
                    for t in trades
                    if t.realized_pnl is not None
                ],
            )
            equity = metrics.equity_curve_from_daily(daily, DEFAULT_STARTING_EQUITY)
            if not equity:
                continue

            series_list.append(
                ComparisonSeriesResponse(
                    id=str(account.id),
                    name=account.name,
                    color=COMPARISON_COLORS[i % len(COMPARISON_COLORS)],
                    points=[
                        EquityPointResponse(date=d, equity=Decimal(str(eq))) for d, eq in equity
                    ],
                ),
            )

        return series_list

    def _symbol_performance(
        self,
        trades: list[Trade],
        journal_entries: list[TradeJournal],
    ) -> list[SymbolPerformanceResponse]:
        buckets: dict[str, list[Decimal]] = defaultdict(list)
        for trade in trades:
            if trade.realized_pnl is None:
                continue
            buckets[trade.symbol].append(trade.realized_pnl)
        for entry in journal_entries:
            if entry.pnl is None or not entry.symbol:
                continue
            buckets[entry.symbol].append(entry.pnl)

        results: list[SymbolPerformanceResponse] = []
        for symbol, symbol_pnls in buckets.items():
            trade_metrics = metrics.compute_trade_metrics(symbol_pnls)
            total = sum(symbol_pnls, Decimal("0"))
            results.append(
                SymbolPerformanceResponse(
                    symbol=symbol,
                    trade_count=len(symbol_pnls),
                    total_pnl=total,
                    win_rate=float(trade_metrics["win_rate"]),
                    avg_pnl=total / len(symbol_pnls) if symbol_pnls else Decimal("0"),
                ),
            )
        return sorted(results, key=lambda r: float(r.total_pnl), reverse=True)[:12]

    def _session_performance(self, trades: list[Trade]) -> list[SessionPerformanceResponse]:
        buckets: dict[str, list[Decimal]] = defaultdict(list)
        for trade in trades:
            if trade.realized_pnl is None or trade.closed_at is None:
                continue
            hour = trade.closed_at.hour
            session = next(
                (name for name, hours in SESSION_HOURS.items() if hour in hours),
                "Other",
            )
            buckets[session].append(trade.realized_pnl)

        results: list[SessionPerformanceResponse] = []
        for session in ["Asia", "London", "New York", "After Hours"]:
            session_pnls = buckets.get(session, [])
            if not session_pnls:
                continue
            trade_metrics = metrics.compute_trade_metrics(session_pnls)
            results.append(
                SessionPerformanceResponse(
                    session=session,
                    trade_count=len(session_pnls),
                    total_pnl=sum(session_pnls, Decimal("0")),
                    win_rate=float(trade_metrics["win_rate"]),
                ),
            )
        return results

    async def _strategy_comparison_series(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: AnalyticsFilterParams,
    ) -> list[ComparisonSeriesResponse]:
        strategies = list(
            (
                await db.scalars(
                    select(Strategy)
                    .where(
                        Strategy.user_id == user_id,
                        Strategy.deleted_at.is_(None),
                    )
                    .order_by(Strategy.created_at)
                    .limit(5),
                )
            ).all(),
        )

        series_list: list[ComparisonSeriesResponse] = []
        for i, strategy in enumerate(strategies):
            strategy_filters = AnalyticsFilterParams(
                date_from=filters.date_from,
                date_to=filters.date_to,
                trading_account_id=filters.trading_account_id,
                strategy_id=strategy.id,
            )
            trades = await self._load_closed_trades(db, user_id, strategy_filters)
            journal_entries = await self._load_journal_entries(db, user_id, strategy_filters)
            trade_dates = self._collect_trade_dates(trades, journal_entries)
            daily = metrics.aggregate_daily_pnls(trade_dates)
            equity = metrics.equity_curve_from_daily(daily, DEFAULT_STARTING_EQUITY)
            if not equity:
                continue

            color = strategy.color or COMPARISON_COLORS[i % len(COMPARISON_COLORS)]
            series_list.append(
                ComparisonSeriesResponse(
                    id=str(strategy.id),
                    name=strategy.name,
                    color=color,
                    points=[
                        EquityPointResponse(date=d, equity=Decimal(str(eq))) for d, eq in equity
                    ],
                ),
            )
        return series_list
