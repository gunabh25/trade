"""Risk rule and breach audit models."""

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import RiskAction, RiskBreachType, RiskMonitorStatus
from tradeflow.db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.trading import TradingAccount
    from tradeflow.db.models.user import User


class RiskRule(Base, TimestampMixin, SoftDeleteMixin):
    """Per-account risk thresholds — fully user-configurable."""

    __tablename__ = "risk_rules"
    __table_args__ = (
        Index("ix_risk_rules_user_id_deleted_at", "user_id", "deleted_at"),
        Index("ix_risk_rules_trading_account_id", "trading_account_id"),
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
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Default")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Loss limits
    daily_loss_limit_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    trailing_drawdown_limit_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    # Position / contract limits
    max_position_size_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_contracts_per_symbol: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_total_contracts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_leverage: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # Symbol filters
    allowed_symbols: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    blocked_symbols: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Trading hours
    trading_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    trading_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    trading_hours_timezone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="America/New_York",
    )

    # Session reset for daily P&L
    session_reset_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Kill switch & automated responses
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_flatten_on_breach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_stop_copying_on_breach: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Extensible config for future rules
    config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="risk_rules")
    trading_account: Mapped["TradingAccount"] = relationship(back_populates="risk_rule")
    breaches: Mapped[list["RiskBreach"]] = relationship(back_populates="risk_rule")


class RiskBreach(Base, TimestampMixin):
    """Append-only audit log for every risk breach."""

    __tablename__ = "risk_breaches"
    __table_args__ = (
        Index("ix_risk_breaches_account_created", "trading_account_id", "created_at"),
        Index("ix_risk_breaches_user_id_created", "user_id", "created_at"),
        Index("ix_risk_breaches_type", "breach_type"),
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
    risk_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("risk_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    trading_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    breach_type: Mapped[RiskBreachType] = mapped_column(String(30), nullable=False)
    action_taken: Mapped[RiskAction] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    limit_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    risk_rule: Mapped["RiskRule | None"] = relationship(back_populates="breaches")


class RiskMonitorSnapshot(Base, TimestampMixin):
    """Periodic snapshot of account risk state for monitoring history."""

    __tablename__ = "risk_monitor_snapshots"
    __table_args__ = (
        Index("ix_risk_snapshots_account_created", "trading_account_id", "created_at"),
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
    status: Mapped[RiskMonitorStatus] = mapped_column(String(20), nullable=False)
    daily_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    drawdown_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    peak_equity: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    current_equity: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    total_open_contracts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_leverage: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)
