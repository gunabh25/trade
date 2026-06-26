import uuid
from datetime import time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradeflow.db.base import Base
from tradeflow.db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from tradeflow.db.models.trading import TradingAccount
    from tradeflow.db.models.user import User


class RiskRule(Base, TimestampMixin, SoftDeleteMixin):
    """Per-account risk thresholds enforced by the copy engine."""

    __tablename__ = "risk_rules"
    __table_args__ = (
        UniqueConstraint(
            "trading_account_id",
            name="uq_risk_rules_trading_account_id",
        ),
        Index("ix_risk_rules_user_id_deleted_at", "user_id", "deleted_at"),
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
    daily_loss_limit_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_contracts_per_symbol: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_total_contracts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trailing_drawdown_limit_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    session_reset_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="risk_rules")
    trading_account: Mapped["TradingAccount"] = relationship(back_populates="risk_rule")
