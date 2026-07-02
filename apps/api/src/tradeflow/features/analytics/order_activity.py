"""Derive analytics inputs from filled orders and live broker positions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradeflow.core.logging import get_logger
from tradeflow.db.enums import OrderStatus
from tradeflow.db.models.trading import Order, TradingAccount
from tradeflow.features.analytics.schemas import AnalyticsFilterParams
from tradeflow.integrations.brokers.manager import BrokerSessionManager

logger = get_logger(__name__)

DEFAULT_STARTING_EQUITY = Decimal("100000")


@dataclass
class ActivitySnapshot:
    """Order fills + open position PnL when closed trades are absent."""

    trade_dates: list[tuple[date, Decimal]] = field(default_factory=list)
    ordered_pnls: list[Decimal] = field(default_factory=list)
    symbol_pnls: dict[str, list[Decimal]] = field(default_factory=dict)
    symbol_unrealized: dict[str, Decimal] = field(default_factory=dict)
    fill_count: int = 0
    starting_equity: Decimal = DEFAULT_STARTING_EQUITY
    unrealized_pnl: Decimal = Decimal("0")


async def build_activity_snapshot(
    db: AsyncSession,
    user_id: UUID,
    session_manager: BrokerSessionManager | None,
    filters: AnalyticsFilterParams,
) -> ActivitySnapshot | None:
    """Build supplemental analytics from copy/order activity and open positions."""
    orders = await _load_filled_orders(db, user_id, filters)
    accounts = await _load_trading_accounts(db, user_id, filters.trading_account_id)

    starting_equity = _sum_balances(accounts)
    unrealized = Decimal("0")
    symbol_unrealized: dict[str, Decimal] = {}

    if session_manager is not None:
        for account in accounts:
            try:
                positions = await session_manager.fetch_positions(
                    account.broker_connection_id,
                    account.external_account_id,
                )
            except Exception as exc:
                logger.debug(
                    "analytics_positions_skip",
                    account_id=str(account.id),
                    error=str(exc),
                )
                continue
            for position in positions:
                pnl = position.unrealized_pnl or Decimal("0")
                unrealized += pnl
                symbol_unrealized[position.symbol] = (
                    symbol_unrealized.get(position.symbol, Decimal("0")) + pnl
                )

    if not orders and unrealized == 0:
        return None

    snapshot = ActivitySnapshot(
        fill_count=len(orders),
        starting_equity=starting_equity if starting_equity > 0 else DEFAULT_STARTING_EQUITY,
        unrealized_pnl=unrealized,
        symbol_unrealized=symbol_unrealized,
    )

    for order in sorted(orders, key=lambda row: row.filled_at or row.created_at):
        ts = order.filled_at or order.created_at
        day = ts.date() if isinstance(ts, datetime) else date.today()
        notional = (order.price or Decimal("0")) * order.filled_quantity
        snapshot.trade_dates.append((day, Decimal("0")))
        snapshot.ordered_pnls.append(Decimal("0"))
        symbols = snapshot.symbol_pnls.setdefault(order.symbol, [])
        symbols.append(notional if notional > 0 else Decimal("1"))

    if unrealized != 0:
        today = datetime.now(tz=UTC).date()
        snapshot.trade_dates.append((today, unrealized))
        snapshot.ordered_pnls.append(unrealized)
        for symbol, pnl in symbol_unrealized.items():
            if pnl == 0:
                continue
            snapshot.symbol_pnls.setdefault(symbol, []).append(pnl)

    return snapshot


async def _load_filled_orders(
    db: AsyncSession,
    user_id: UUID,
    filters: AnalyticsFilterParams,
) -> list[Order]:
    query = select(Order).where(
        Order.user_id == user_id,
        Order.deleted_at.is_(None),
        Order.status.in_((OrderStatus.FILLED, OrderStatus.PARTIAL)),
        Order.filled_quantity > 0,
    )
    if filters.trading_account_id:
        query = query.where(Order.trading_account_id == filters.trading_account_id)
    if filters.date_from:
        query = query.where(func.date(Order.created_at) >= filters.date_from)
    if filters.date_to:
        query = query.where(func.date(Order.created_at) <= filters.date_to)

    return list((await db.scalars(query.order_by(Order.created_at))).all())


async def _load_trading_accounts(
    db: AsyncSession,
    user_id: UUID,
    trading_account_id: UUID | None,
) -> list[TradingAccount]:
    query = select(TradingAccount).where(
        TradingAccount.user_id == user_id,
        TradingAccount.deleted_at.is_(None),
    )
    if trading_account_id:
        query = query.where(TradingAccount.id == trading_account_id)
    return list((await db.scalars(query)).all())


def _sum_balances(accounts: list[TradingAccount]) -> Decimal:
    total = Decimal("0")
    for account in accounts:
        if account.balance is not None and account.balance > 0:
            total += account.balance
    return total
