"""Copy trading domain models — groups, followers, events, mappings, execution logs."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import (
    CopyEventAction,
    CopyEventResult,
    CopyFollowerStatus,
    CopyGroupMode,
    CopyGroupStatus,
    CopyMode,
    ExecutionLogStatus,
    OrderLegType,
)
from tradeflow.db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.trading import Order, TradingAccount
    from tradeflow.db.models.user import User


class CopyGroup(Base, TimestampMixin, SoftDeleteMixin):
    """Leader + follower configuration for a copy session."""

    __tablename__ = "copy_groups"
    __table_args__ = (
        Index("ix_copy_groups_user_id_deleted_at", "user_id", "deleted_at"),
        Index("ix_copy_groups_status", "status"),
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
    leader_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[CopyGroupMode] = mapped_column(
        String(20),
        nullable=False,
        default=CopyGroupMode.LIVE,
    )
    status: Mapped[CopyGroupStatus] = mapped_column(
        String(20),
        nullable=False,
        default=CopyGroupStatus.DRAFT,
    )
    copying_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sim_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="copy_groups")
    leader_account: Mapped["TradingAccount"] = relationship(
        foreign_keys=[leader_account_id],
    )
    followers: Mapped[list["CopyGroupFollower"]] = relationship(back_populates="copy_group")
    events: Mapped[list["CopyEvent"]] = relationship(back_populates="copy_group")
    order_mappings: Mapped[list["OrderMapping"]] = relationship(back_populates="copy_group")


class CopyGroupFollower(Base, TimestampMixin, SoftDeleteMixin):
    """Follower account attached to a copy group with sizing configuration."""

    __tablename__ = "copy_group_followers"
    __table_args__ = (
        UniqueConstraint(
            "copy_group_id",
            "follower_account_id",
            name="uq_copy_group_followers_group_account",
        ),
        Index("ix_copy_group_followers_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    copy_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copy_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    follower_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    copy_mode: Mapped[CopyMode] = mapped_column(String(30), nullable=False)
    sizing_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    status: Mapped[CopyFollowerStatus] = mapped_column(
        String(20),
        nullable=False,
        default=CopyFollowerStatus.ACTIVE,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lock_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    copy_group: Mapped["CopyGroup"] = relationship(back_populates="followers")
    follower_account: Mapped["TradingAccount"] = relationship(
        foreign_keys=[follower_account_id],
    )


class CopyEvent(Base, TimestampMixin):
    """Append-only audit stream for every copy action (success, failure, skip)."""

    __tablename__ = "copy_events"
    __table_args__ = (
        Index("ix_copy_events_group_created", "copy_group_id", "created_at"),
        Index("ix_copy_events_leader_event_id", "leader_event_id"),
        Index("ix_copy_events_user_id_created", "user_id", "created_at"),
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
    copy_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copy_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    leader_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    follower_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    leader_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    leader_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    follower_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[CopyEventAction] = mapped_column(String(20), nullable=False)
    result: Mapped[CopyEventResult] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leader_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    follower_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    slippage: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    copy_group: Mapped["CopyGroup"] = relationship(back_populates="events")


class OrderMapping(Base, TimestampMixin):
    """Leader → follower order ID lookup for modify/cancel/bracket legs."""

    __tablename__ = "order_mappings"
    __table_args__ = (
        UniqueConstraint(
            "copy_group_id",
            "leader_order_id",
            "follower_account_id",
            "leg_type",
            name="uq_order_mappings_lookup",
        ),
        Index("ix_order_mappings_leader_order", "copy_group_id", "leader_order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    copy_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copy_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    leader_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    follower_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    follower_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    leader_order_db_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    follower_order_db_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    leg_type: Mapped[OrderLegType] = mapped_column(
        String(20),
        nullable=False,
        default=OrderLegType.ENTRY,
    )
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    copy_group: Mapped["CopyGroup"] = relationship(back_populates="order_mappings")
    leader_order: Mapped["Order | None"] = relationship(foreign_keys=[leader_order_db_id])
    follower_order: Mapped["Order | None"] = relationship(foreign_keys=[follower_order_db_id])


class ExecutionLog(Base, TimestampMixin):
    """Detailed execution log with retry tracking for copy operations."""

    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("ix_execution_logs_status_created", "status", "created_at"),
        Index("ix_execution_logs_copy_group_id", "copy_group_id", "created_at"),
        Index("ix_execution_logs_leader_event_id", "leader_event_id"),
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
    copy_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copy_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    follower_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    leader_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    leader_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[CopyEventAction] = mapped_column(String(20), nullable=False)
    status: Mapped[ExecutionLogStatus] = mapped_column(String(20), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
