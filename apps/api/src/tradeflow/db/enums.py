from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "admin"
    TRADER = "trader"
    SUPPORT = "support"


class OAuthProvider(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    MICROSOFT = "microsoft"


class VerificationTokenType(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR_LOGIN = "two_factor_login"


class BrokerType(StrEnum):
    PAPER = "paper"
    BINANCE = "binance"
    BYBIT = "bybit"
    OANDA = "oanda"
    INTERACTIVE_BROKERS = "interactive_brokers"
    TRADOVATE = "tradovate"
    TRADINGVIEW = "tradingview"
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
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDED = "trial_ended"
    COUPON_APPLIED = "coupon_applied"


class BillingEventStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class CouponDiscountType(StrEnum):
    PERCENT = "percent"
    AMOUNT = "amount"


class CouponDuration(StrEnum):
    ONCE = "once"
    REPEATING = "repeating"
    FOREVER = "forever"


class UsageMetric(StrEnum):
    TRADING_ACCOUNTS = "trading_accounts"
    BROKER_CONNECTIONS = "broker_connections"
    COPY_GROUPS = "copy_groups"
    API_REQUESTS = "api_requests"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class CopyMode(StrEnum):
    """How follower order size is derived from the leader order."""

    FIXED_QUANTITY = "fixed_quantity"
    RISK_MULTIPLIER = "risk_multiplier"
    PERCENTAGE_ALLOCATION = "percentage_allocation"
    REVERSE_COPY = "reverse_copy"


class CopyGroupStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class CopyGroupMode(StrEnum):
    SIM = "sim"
    LIVE = "live"


class CopyFollowerStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    LOCKED = "locked"


class CopyEventAction(StrEnum):
    PLACE = "place"
    MODIFY = "modify"
    CANCEL = "cancel"
    FILL = "fill"
    PARTIAL_FILL = "partial_fill"
    FLATTEN = "flatten"
    BREACH = "breach"


class CopyEventResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    SIMULATED = "simulated"
    RETRYING = "retrying"


class OrderLegType(StrEnum):
    ENTRY = "entry"
    STOP = "stop"
    TARGET = "target"
    TRAILING = "trailing"


class ExecutionLogStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"
    DEAD_LETTER = "dead_letter"


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
    JOURNAL_ENTRY = "journal_entry"
    STRATEGY = "strategy"
    TRADING_ACCOUNT = "trading_account"
    ORDER = "order"


class JournalSource(StrEnum):
    MANUAL = "manual"
    AUTO_IMPORT = "auto_import"


class TradeEmotion(StrEnum):
    CONFIDENT = "confident"
    CALM = "calm"
    FOMO = "fomo"
    FEARFUL = "fearful"
    REVENGE = "revenge"
    IMPATIENT = "impatient"
    DISCIPLINED = "disciplined"
    ANXIOUS = "anxious"


class NotificationType(StrEnum):
    TRADE_COPIED = "trade_copied"
    COPY_FAILURE = "copy_failure"
    CONNECTION_LOST = "connection_lost"
    RISK_BREACH = "risk_breach"
    POSITION_DRIFT = "position_drift"
    KILL_SWITCH = "kill_switch"
    BILLING = "billing"
    PNL_MILESTONE = "pnl_milestone"
    SYSTEM = "system"


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    PUSH = "push"


class NotificationEvent(StrEnum):
    TRADE_COPIED = "trade_copied"
    TRADE_FAILED = "trade_failed"
    BROKER_OFFLINE = "broker_offline"
    RISK_ALERT = "risk_alert"
    SUBSCRIPTION_EXPIRY = "subscription_expiry"
    PNL_MILESTONE = "pnl_milestone"


class RiskBreachType(StrEnum):
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_POSITION_SIZE = "max_position_size"
    MAX_CONTRACTS = "max_contracts"
    MAX_CONTRACTS_PER_SYMBOL = "max_contracts_per_symbol"
    TRADING_HOURS = "trading_hours"
    ALLOWED_SYMBOLS = "allowed_symbols"
    BLOCKED_SYMBOLS = "blocked_symbols"
    LEVERAGE_LIMIT = "leverage_limit"
    KILL_SWITCH = "kill_switch"


class RiskAction(StrEnum):
    BLOCK = "block"
    WARN = "warn"
    FLATTEN = "flatten"
    STOP_COPYING = "stop_copying"
    LOCK_ACCOUNT = "lock_account"


class RiskMonitorStatus(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    BREACHED = "breached"
    KILL_SWITCH = "kill_switch"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    COPY = "copy"
    BREACH = "breach"
    EXPORT = "export"
    ADMIN = "admin"


class SupportTicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SystemLogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
