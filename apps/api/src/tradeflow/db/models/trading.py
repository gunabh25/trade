import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    TradeSide,
    TradeStatus,
    TradingAccountRole,
    TradingAccountStatus,
    TradingAccountType,
)
from tradeflow.db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.broker import BrokerConnection
    from tradeflow.db.models.journal import Strategy, TradeJournal
    from tradeflow.db.models.risk import RiskRule
    from tradeflow.db.models.user import User


class TradingAccount(Base, TimestampMixin, SoftDeleteMixin):
    """Individual broker account used for copying (leader or follower)."""

    __tablename__ = "trading_accounts"
    __table_args__ = (
        Index("ix_trading_accounts_user_id_deleted_at", "user_id", "deleted_at"),
        Index(
            "ix_trading_accounts_broker_connection_id_deleted_at",
            "broker_connection_id",
            "deleted_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("broker_connections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    external_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[TradingAccountType] = mapped_column(String(30), nullable=False)
    account_role: Mapped[TradingAccountRole] = mapped_column(String(30), nullable=False)
    status: Mapped[TradingAccountStatus] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="trading_accounts")
    broker_connection: Mapped["BrokerConnection"] = relationship(
        back_populates="trading_accounts",
    )
    risk_rule: Mapped["RiskRule | None"] = relationship(
        back_populates="trading_account",
        uselist=False,
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="trading_account")
    trades: Mapped[list["Trade"]] = relationship(back_populates="trading_account")
    positions: Mapped[list["Position"]] = relationship(back_populates="trading_account")
    trade_journals: Mapped[list["TradeJournal"]] = relationship(
        back_populates="trading_account",
    )


class Order(Base, TimestampMixin, SoftDeleteMixin):
    """Submitted or copied order intent on a trading account."""

    __tablename__ = "orders"
    __table_args__ = (
        Index(
            "ix_orders_trading_account_id_status_created_at",
            "trading_account_id",
            "status",
            "created_at",
        ),
        Index("ix_orders_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    trading_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategies.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[OrderSide] = mapped_column(String(10), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(String(20), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    filled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders")
    trading_account: Mapped["TradingAccount"] = relationship(back_populates="orders")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="orders")
    parent_order: Mapped["Order | None"] = relationship(
        remote_side="Order.id",
        back_populates="child_orders",
    )
    child_orders: Mapped[list["Order"]] = relationship(back_populates="parent_order")
    trades: Mapped[list["Trade"]] = relationship(back_populates="order")


class Trade(Base, TimestampMixin, SoftDeleteMixin):
    """Executed trade lifecycle — entry through exit with realized P&L."""

    __tablename__ = "trades"
    __table_args__ = (
        Index(
            "ix_trades_trading_account_id_status_opened_at",
            "trading_account_id",
            "status",
            "opened_at",
        ),
        Index("ix_trades_user_id_opened_at", "user_id", "opened_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    trading_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategies.id", ondelete="SET NULL"),
        nullable=True,
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[TradeSide] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    status: Mapped[TradeStatus] = mapped_column(String(20), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="trades")
    trading_account: Mapped["TradingAccount"] = relationship(back_populates="trades")
    order: Mapped["Order | None"] = relationship(back_populates="trades")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="trades")
    trade_journals: Mapped[list["TradeJournal"]] = relationship(back_populates="trade")


class Position(Base, TimestampMixin, SoftDeleteMixin):
    """Current open position snapshot per account and symbol."""

    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_trading_account_id_deleted_at", "trading_account_id", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    trading_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[PositionSide] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    trading_account: Mapped["TradingAccount"] = relationship(back_populates="positions")
