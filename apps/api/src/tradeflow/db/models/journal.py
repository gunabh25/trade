import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.enums import JournalSource, NoteEntityType, TradeSide
from tradeflow.db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.trading import Order, Trade, TradingAccount
    from tradeflow.db.models.user import User


class Strategy(Base, TimestampMixin, SoftDeleteMixin):
    """User-defined trading strategy metadata and configuration."""

    __tablename__ = "strategies"
    __table_args__ = (Index("ix_strategies_user_id_deleted_at", "user_id", "deleted_at"),)

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
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    symbols: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default="#22c55e")
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="strategies")
    orders: Mapped[list["Order"]] = relationship(back_populates="strategy")
    trades: Mapped[list["Trade"]] = relationship(back_populates="strategy")
    journal_entries: Mapped[list["TradeJournal"]] = relationship(back_populates="strategy")


class TradeJournal(Base, TimestampMixin, SoftDeleteMixin):
    """Structured journal entry for reviewing trades and trading sessions."""

    __tablename__ = "trade_journals"
    __table_args__ = (
        Index("ix_trade_journals_user_id_session_date", "user_id", "session_date"),
        Index("ix_trade_journals_user_id_symbol", "user_id", "symbol"),
        Index("ix_trade_journals_strategy_id", "strategy_id"),
        Index("ix_trade_journals_trade_id", "trade_id"),
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
    trading_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    trade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trades.id", ondelete="SET NULL"),
        nullable=True,
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategies.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    emotions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    mistakes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[JournalSource] = mapped_column(
        String(20),
        nullable=False,
        default=JournalSource.MANUAL,
    )
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    side: Mapped[TradeSide | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="trade_journals")
    trading_account: Mapped["TradingAccount | None"] = relationship(
        back_populates="trade_journals",
    )
    trade: Mapped["Trade | None"] = relationship(back_populates="trade_journals")
    strategy: Mapped["Strategy | None"] = relationship(back_populates="journal_entries")
    screenshots: Mapped[list["JournalScreenshot"]] = relationship(
        back_populates="journal_entry",
        cascade="all, delete-orphan",
    )


class JournalScreenshot(Base, TimestampMixin):
    """Screenshot attachments for journal entries."""

    __tablename__ = "journal_screenshots"
    __table_args__ = (Index("ix_journal_screenshots_journal_id", "journal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    journal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trade_journals.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    journal_entry: Mapped["TradeJournal"] = relationship(back_populates="screenshots")


class Note(Base, TimestampMixin, SoftDeleteMixin):
    """Polymorphic free-form notes attached to trades, journals, strategies, or accounts."""

    __tablename__ = "notes"
    __table_args__ = (Index("ix_notes_user_id_entity", "user_id", "entity_type", "entity_id"),)

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
    entity_type: Mapped[NoteEntityType] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="notes")
