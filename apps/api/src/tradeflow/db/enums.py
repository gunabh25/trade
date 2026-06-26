from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "admin"
    TRADER = "trader"
    SUPPORT = "support"


class OAuthProvider(StrEnum):
    GOOGLE = "google"
    APPLE = "apple"
    MICROSOFT = "microsoft"


class BrokerType(StrEnum):
    TRADOVATE = "tradovate"
    RITHMIC = "rithmic"
    NINJATRADER = "ninjatrader"
    PROJECTX = "projectx"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class TradingAccountType(StrEnum):
    LIVE = "live"
    SIM = "sim"
    EVALUATION = "evaluation"
    FUNDED = "funded"


class TradingAccountRole(StrEnum):
    LEADER = "leader"
    FOLLOWER = "follower"
    UNASSIGNED = "unassigned"


class TradingAccountStatus(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"
    PAUSED = "paused"
    SUSPENDED = "suspended"


class PlanInterval(StrEnum):
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class BillingEventType(StrEnum):
    INVOICE_PAID = "invoice_paid"
    INVOICE_FAILED = "invoice_failed"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    REFUND = "refund"


class BillingEventStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TradeSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class TradeStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class NoteEntityType(StrEnum):
    TRADE = "trade"
    JOURNAL = "journal"
    STRATEGY = "strategy"
    TRADING_ACCOUNT = "trading_account"
    ORDER = "order"


class NotificationType(StrEnum):
    COPY_FAILURE = "copy_failure"
    CONNECTION_LOST = "connection_lost"
    RISK_BREACH = "risk_breach"
    POSITION_DRIFT = "position_drift"
    BILLING = "billing"
    SYSTEM = "system"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    COPY = "copy"
    BREACH = "breach"
    EXPORT = "export"
