"""Trading journal business logic."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.errors import NotFoundError
from tradeflow.core.logging import get_logger
from tradeflow.db.enums import JournalSource, TradeStatus
from tradeflow.db.models.journal import JournalScreenshot, Strategy, TradeJournal
from tradeflow.db.models.trading import Trade
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

logger = get_logger(__name__)


class JournalService:
    """CRUD, import, search, filters, statistics for the trading journal."""

    async def create_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateJournalEntryRequest,
    ) -> JournalEntryResponse:
        entry = TradeJournal(
            user_id=user_id,
            title=payload.title,
            session_date=payload.session_date,
            content=payload.content,
            notes=payload.notes,
            mood=payload.mood,
            pnl=payload.pnl,
            tags=payload.tags,
            emotions=[str(e) for e in payload.emotions] if payload.emotions else None,
            mistakes=payload.mistakes,
            lessons_learned=payload.lessons_learned,
            symbol=payload.symbol,
            side=payload.side,
            quantity=payload.quantity,
            entry_price=payload.entry_price,
            exit_price=payload.exit_price,
            trade_id=payload.trade_id,
            strategy_id=payload.strategy_id,
            trading_account_id=payload.trading_account_id,
            source=JournalSource.MANUAL,
        )
        db.add(entry)
        await db.flush()
        return await self._load_entry(db, user_id, entry.id)

    async def update_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
        payload: UpdateJournalEntryRequest,
    ) -> JournalEntryResponse:
        entry = await self._get_entry(db, user_id, entry_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "emotions" and value is not None:
                setattr(entry, field, [str(v) for v in value])
            else:
                setattr(entry, field, value)
        await db.flush()
        return await self._load_entry(db, user_id, entry_id)

    async def delete_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        entry = await self._get_entry(db, user_id, entry_id)
        entry.deleted_at = datetime.now(tz=UTC)

    async def get_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> JournalEntryResponse:
        return await self._load_entry(db, user_id, entry_id)

    async def list_entries(
        self,
        db: AsyncSession,
        user_id: UUID,
        filters: JournalFilterParams,
    ) -> tuple[list[JournalEntryResponse], int]:
        query = (
            select(TradeJournal)
            .options(
                selectinload(TradeJournal.screenshots),
                selectinload(TradeJournal.strategy),
            )
            .where(TradeJournal.user_id == user_id, TradeJournal.deleted_at.is_(None))
        )
        query = self._apply_filters(query, filters)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(TradeJournal.session_date.desc(), TradeJournal.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)

        entries = await db.scalars(query)
        return [self._to_response(e) for e in entries.all()], total

    async def import_trades(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: ImportTradesRequest,
    ) -> ImportTradesResponse:
        """Auto-import closed trades that don't have journal entries yet."""
        existing_trade_ids = await db.scalars(
            select(TradeJournal.trade_id).where(
                TradeJournal.user_id == user_id,
                TradeJournal.trade_id.isnot(None),
                TradeJournal.deleted_at.is_(None),
            ),
        )
        existing = {tid for tid in existing_trade_ids.all() if tid}

        trade_query = select(Trade).where(
            Trade.user_id == user_id,
            Trade.status == TradeStatus.CLOSED,
            Trade.deleted_at.is_(None),
        )
        if payload.trading_account_id:
            trade_query = trade_query.where(
                Trade.trading_account_id == payload.trading_account_id,
            )
        if payload.since:
            since_dt = datetime.combine(payload.since, time.min, tzinfo=UTC)
            trade_query = trade_query.where(Trade.closed_at >= since_dt)

        trades = await db.scalars(trade_query)
        imported = 0
        skipped = 0

        for trade in trades.all():
            if trade.id in existing:
                skipped += 1
                continue

            session_date = trade.closed_at.date() if trade.closed_at else trade.opened_at.date()
            entry = TradeJournal(
                user_id=user_id,
                trading_account_id=trade.trading_account_id,
                trade_id=trade.id,
                strategy_id=trade.strategy_id,
                title=f"{trade.symbol} {trade.side.value.upper()}",
                session_date=session_date,
                pnl=trade.realized_pnl,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                source=JournalSource.AUTO_IMPORT,
                tags=["auto-import"],
            )
            db.add(entry)
            imported += 1

        await db.flush()
        logger.info("journal_trades_imported", user_id=str(user_id), imported=imported)
        return ImportTradesResponse(imported=imported, skipped=skipped)

    async def get_calendar(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        year: int,
        month: int,
    ) -> list[CalendarDayResponse]:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        rows = await db.execute(
            select(
                TradeJournal.session_date,
                func.sum(TradeJournal.pnl),
                func.count(TradeJournal.id),
            )
            .where(
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
                TradeJournal.session_date >= start,
                TradeJournal.session_date < end,
            )
            .group_by(TradeJournal.session_date)
            .order_by(TradeJournal.session_date),
        )
        return [
            CalendarDayResponse(
                date=row[0],
                pnl=row[1] or Decimal("0"),
                trade_count=row[2],
            )
            for row in rows.all()
        ]

    async def get_stats(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> JournalStatsResponse:
        query = select(TradeJournal).where(
            TradeJournal.user_id == user_id,
            TradeJournal.deleted_at.is_(None),
            TradeJournal.pnl.isnot(None),
        )
        if date_from:
            query = query.where(TradeJournal.session_date >= date_from)
        if date_to:
            query = query.where(TradeJournal.session_date <= date_to)

        entries = (await db.scalars(query)).all()
        pnls = [e.pnl for e in entries if e.pnl is not None]

        if not pnls:
            return JournalStatsResponse(
                total_entries=len(entries),
                total_pnl=Decimal("0"),
                win_count=0,
                loss_count=0,
                breakeven_count=0,
                win_rate=0.0,
                avg_win=Decimal("0"),
                avg_loss=Decimal("0"),
                profit_factor=None,
                best_trade=None,
                worst_trade=None,
                avg_rr=None,
            )

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        breakeven = [p for p in pnls if p == 0]

        gross_profit = sum(wins, Decimal("0"))
        gross_loss = abs(sum(losses, Decimal("0")))

        return JournalStatsResponse(
            total_entries=len(entries),
            total_pnl=sum(pnls, Decimal("0")),
            win_count=len(wins),
            loss_count=len(losses),
            breakeven_count=len(breakeven),
            win_rate=len(wins) / len(pnls) * 100 if pnls else 0.0,
            avg_win=gross_profit / len(wins) if wins else Decimal("0"),
            avg_loss=gross_loss / len(losses) if losses else Decimal("0"),
            profit_factor=float(gross_profit / gross_loss) if gross_loss else None,
            best_trade=max(pnls),
            worst_trade=min(pnls),
            avg_rr=float(gross_profit / gross_loss) if gross_loss else None,
        )

    async def get_strategy_performance(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[StrategyPerformanceResponse]:
        entries = await db.scalars(
            select(TradeJournal)
            .options(selectinload(TradeJournal.strategy))
            .where(
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
                TradeJournal.pnl.isnot(None),
            ),
        )

        by_strategy: dict[str | None, list[TradeJournal]] = {}
        for entry in entries.all():
            key = str(entry.strategy_id) if entry.strategy_id else None
            by_strategy.setdefault(key, []).append(entry)

        results: list[StrategyPerformanceResponse] = []
        for _key, group in by_strategy.items():
            pnls = [e.pnl for e in group if e.pnl is not None]
            wins = sum(1 for p in pnls if p > 0)
            strategy = group[0].strategy
            results.append(
                StrategyPerformanceResponse(
                    strategy_id=group[0].strategy_id,
                    strategy_name=strategy.name if strategy else "Unassigned",
                    color=strategy.color if strategy else "#64748b",
                    trade_count=len(group),
                    total_pnl=sum(pnls, Decimal("0")),
                    win_rate=wins / len(pnls) * 100 if pnls else 0.0,
                    avg_pnl=sum(pnls, Decimal("0")) / len(pnls) if pnls else Decimal("0"),
                ),
            )
        return sorted(results, key=lambda r: r.total_pnl, reverse=True)

    async def get_emotion_stats(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[EmotionStatsResponse]:
        entries = await db.scalars(
            select(TradeJournal).where(
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
                TradeJournal.emotions.isnot(None),
            ),
        )

        by_emotion: dict[str, list[Decimal]] = {}
        for entry in entries.all():
            if not entry.emotions:
                continue
            pnl = entry.pnl or Decimal("0")
            for emotion in entry.emotions:
                by_emotion.setdefault(emotion, []).append(pnl)

        return [
            EmotionStatsResponse(
                emotion=emotion,
                count=len(pnls),
                total_pnl=sum(pnls, Decimal("0")),
                win_rate=sum(1 for p in pnls if p > 0) / len(pnls) * 100,
            )
            for emotion, pnls in sorted(by_emotion.items(), key=lambda x: -len(x[1]))
        ]

    async def list_tags(self, db: AsyncSession, user_id: UUID) -> list[str]:
        entries = await db.scalars(
            select(TradeJournal.tags).where(
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
                TradeJournal.tags.isnot(None),
            ),
        )
        tags: set[str] = set()
        for tag_list in entries.all():
            if tag_list:
                tags.update(tag_list)
        return sorted(tags)

    async def add_screenshot(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
        payload: AddScreenshotRequest,
    ) -> ScreenshotResponse:
        entry = await self._get_entry(db, user_id, entry_id)
        count = len(entry.screenshots)
        screenshot = JournalScreenshot(
            journal_id=entry.id,
            file_url=payload.file_url,
            caption=payload.caption,
            sort_order=count,
        )
        db.add(screenshot)
        await db.flush()
        await db.refresh(screenshot)
        return ScreenshotResponse.model_validate(screenshot)

    async def create_strategy(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: CreateStrategyRequest,
    ) -> StrategyResponse:
        strategy = Strategy(user_id=user_id, **payload.model_dump())
        db.add(strategy)
        await db.flush()
        await db.refresh(strategy)
        return StrategyResponse.model_validate(strategy)

    async def update_strategy(
        self,
        db: AsyncSession,
        user_id: UUID,
        strategy_id: UUID,
        payload: UpdateStrategyRequest,
    ) -> StrategyResponse:
        strategy = await self._get_strategy(db, user_id, strategy_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(strategy, field, value)
        await db.flush()
        await db.refresh(strategy)
        return StrategyResponse.model_validate(strategy)

    async def list_strategies(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[StrategyResponse]:
        strategies = await db.scalars(
            select(Strategy).where(
                Strategy.user_id == user_id,
                Strategy.deleted_at.is_(None),
            ),
        )
        return [StrategyResponse.model_validate(s) for s in strategies.all()]

    async def _get_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> TradeJournal:
        entry = await db.scalar(
            select(TradeJournal).where(
                TradeJournal.id == entry_id,
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
            ),
        )
        if entry is None:
            raise NotFoundError("Journal entry not found")
        return entry

    async def _load_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> JournalEntryResponse:
        entry = await db.scalar(
            select(TradeJournal)
            .options(
                selectinload(TradeJournal.screenshots),
                selectinload(TradeJournal.strategy),
            )
            .where(
                TradeJournal.id == entry_id,
                TradeJournal.user_id == user_id,
                TradeJournal.deleted_at.is_(None),
            ),
        )
        if entry is None:
            raise NotFoundError("Journal entry not found")
        return self._to_response(entry)

    async def _get_strategy(
        self,
        db: AsyncSession,
        user_id: UUID,
        strategy_id: UUID,
    ) -> Strategy:
        strategy = await db.scalar(
            select(Strategy).where(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id,
                Strategy.deleted_at.is_(None),
            ),
        )
        if strategy is None:
            raise NotFoundError("Strategy not found")
        return strategy

    @staticmethod
    def _apply_filters(query: object, filters: JournalFilterParams) -> object:
        q = query
        if filters.q:
            pattern = f"%{filters.q}%"
            q = q.where(  # type: ignore[union-attr]
                or_(
                    TradeJournal.title.ilike(pattern),
                    TradeJournal.content.ilike(pattern),
                    TradeJournal.notes.ilike(pattern),
                    TradeJournal.lessons_learned.ilike(pattern),
                    TradeJournal.symbol.ilike(pattern),
                ),
            )
        if filters.strategy_id:
            q = q.where(TradeJournal.strategy_id == filters.strategy_id)  # type: ignore[union-attr]
        if filters.symbol:
            q = q.where(TradeJournal.symbol.ilike(filters.symbol))  # type: ignore[union-attr]
        if filters.tag:
            q = q.where(TradeJournal.tags.contains([filters.tag]))  # type: ignore[union-attr]
        if filters.emotion:
            q = q.where(TradeJournal.emotions.contains([filters.emotion]))  # type: ignore[union-attr]
        if filters.date_from:
            q = q.where(TradeJournal.session_date >= filters.date_from)  # type: ignore[union-attr]
        if filters.date_to:
            q = q.where(TradeJournal.session_date <= filters.date_to)  # type: ignore[union-attr]
        if filters.source:
            q = q.where(TradeJournal.source == filters.source)  # type: ignore[union-attr]
        return q

    @staticmethod
    def _to_response(entry: TradeJournal) -> JournalEntryResponse:
        return JournalEntryResponse(
            id=entry.id,
            title=entry.title,
            content=entry.content,
            notes=entry.notes,
            mood=entry.mood,
            session_date=entry.session_date,
            pnl=entry.pnl,
            tags=entry.tags,
            emotions=entry.emotions,
            mistakes=entry.mistakes,
            lessons_learned=entry.lessons_learned,
            source=entry.source,
            symbol=entry.symbol,
            side=entry.side,
            quantity=entry.quantity,
            entry_price=entry.entry_price,
            exit_price=entry.exit_price,
            trade_id=entry.trade_id,
            strategy_id=entry.strategy_id,
            trading_account_id=entry.trading_account_id,
            strategy=StrategyResponse.model_validate(entry.strategy) if entry.strategy else None,
            screenshots=[ScreenshotResponse.model_validate(s) for s in entry.screenshots],
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
