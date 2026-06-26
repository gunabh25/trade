"""SQLAlchemy ORM models — import all models so Alembic discovers metadata."""

from tradeflow.db.models.api_key import ApiKey
from tradeflow.db.models.audit import AuditLog
from tradeflow.db.models.auth import RefreshToken, VerificationToken
from tradeflow.db.models.billing import BillingEvent, Plan, Subscription
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.copy_trading import (
    CopyEvent,
    CopyGroup,
    CopyGroupFollower,
    ExecutionLog,
    OrderMapping,
)
from tradeflow.db.models.journal import Note, Strategy, TradeJournal
from tradeflow.db.models.notification import Notification
from tradeflow.db.models.oauth import OAuthAccount
from tradeflow.db.models.risk import RiskBreach, RiskMonitorSnapshot, RiskRule
from tradeflow.db.models.session import Session
from tradeflow.db.models.trading import Order, Position, Trade, TradingAccount
from tradeflow.db.models.user import Role, User, UserRole

__all__ = [
    "ApiKey",
    "AuditLog",
    "BillingEvent",
    "BrokerConnection",
    "CopyEvent",
    "CopyGroup",
    "CopyGroupFollower",
    "ExecutionLog",
    "Note",
    "Notification",
    "OAuthAccount",
    "Order",
    "OrderMapping",
    "Plan",
    "Position",
    "RefreshToken",
    "RiskBreach",
    "RiskMonitorSnapshot",
    "RiskRule",
    "Role",
    "Session",
    "Strategy",
    "Subscription",
    "Trade",
    "TradeJournal",
    "TradingAccount",
    "User",
    "UserRole",
    "VerificationToken",
]
