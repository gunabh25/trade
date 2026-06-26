"""SQLAlchemy ORM models — import all models so Alembic discovers metadata."""

from tradeflow.db.models.admin_ops import Announcement, FeatureFlag, SupportTicket, SystemLogEntry
from tradeflow.db.models.api_key import ApiKey
from tradeflow.db.models.audit import AuditLog
from tradeflow.db.models.auth import RefreshToken, VerificationToken
from tradeflow.db.models.billing import (
    BillingEvent,
    Coupon,
    Invoice,
    Plan,
    Subscription,
    UsageRecord,
)
from tradeflow.db.models.broker import BrokerConnection
from tradeflow.db.models.copy_trading import (
    CopyEvent,
    CopyGroup,
    CopyGroupFollower,
    ExecutionLog,
    OrderMapping,
)
from tradeflow.db.models.journal import JournalScreenshot, Note, Strategy, TradeJournal
from tradeflow.db.models.notification import Notification
from tradeflow.db.models.notification_settings import (
    NotificationChannelSetting,
    NotificationPreference,
)
from tradeflow.db.models.oauth import OAuthAccount
from tradeflow.db.models.risk import RiskBreach, RiskMonitorSnapshot, RiskRule
from tradeflow.db.models.session import Session
from tradeflow.db.models.trading import Order, Position, Trade, TradingAccount
from tradeflow.db.models.user import Role, User, UserRole

__all__ = [
    "Announcement",
    "ApiKey",
    "AuditLog",
    "BillingEvent",
    "BrokerConnection",
    "CopyEvent",
    "CopyGroup",
    "CopyGroupFollower",
    "Coupon",
    "ExecutionLog",
    "FeatureFlag",
    "Invoice",
    "JournalScreenshot",
    "Note",
    "Notification",
    "NotificationChannelSetting",
    "NotificationPreference",
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
    "SupportTicket",
    "SystemLogEntry",
    "Trade",
    "TradeJournal",
    "TradingAccount",
    "UsageRecord",
    "User",
    "UserRole",
    "VerificationToken",
]
