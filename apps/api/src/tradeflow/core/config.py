from typing import Self

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="TradeFlow AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_secret_key: str = Field(alias="API_SECRET_KEY")
    api_cors_origins: str = Field(
        default="http://localhost:3000",
        alias="API_CORS_ORIGINS",
    )
    api_log_level: str = Field(default="INFO", alias="API_LOG_LEVEL")
    api_log_format: str = Field(default="json", alias="API_LOG_FORMAT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    api_graceful_shutdown_seconds: int = Field(default=30, alias="API_GRACEFUL_SHUTDOWN_SECONDS")
    api_trusted_hosts: str = Field(default="", alias="API_TRUSTED_HOSTS")
    api_rate_limit_per_minute: int = Field(default=300, alias="API_RATE_LIMIT_PER_MINUTE")
    api_enable_gzip: bool = Field(default=True, alias="API_ENABLE_GZIP")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    # Observability
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    sentry_environment: str | None = Field(default=None, alias="SENTRY_ENVIRONMENT")
    sentry_traces_sample_rate: float = Field(default=0.1, alias="SENTRY_TRACES_SAMPLE_RATE")
    sentry_profiles_sample_rate: float = Field(default=0.1, alias="SENTRY_PROFILES_SAMPLE_RATE")

    # JWT issuer/audience (production hardening)
    jwt_issuer: str = Field(default="tradeflow-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="tradeflow-web", alias="JWT_AUDIENCE")

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_url_sync: PostgresDsn = Field(alias="DATABASE_URL_SYNC")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")

    redis_url: RedisDsn = Field(alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")

    celery_broker_url: RedisDsn = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: RedisDsn = Field(alias="CELERY_RESULT_BACKEND")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")

    # Auth / JWT
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    )
    auth_access_cookie_name: str = Field(default="tf_access", alias="AUTH_ACCESS_COOKIE_NAME")
    auth_refresh_cookie_name: str = Field(default="tf_refresh", alias="AUTH_REFRESH_COOKIE_NAME")
    auth_csrf_cookie_name: str = Field(default="tf_csrf", alias="AUTH_CSRF_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="AUTH_COOKIE_SAMESITE")
    auth_cookie_domain: str | None = Field(default=None, alias="AUTH_COOKIE_DOMAIN")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # OAuth
    google_oauth_client_id: str | None = Field(default=None, alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str | None = Field(
        default=None,
        alias="GOOGLE_OAUTH_CLIENT_SECRET",
    )
    github_oauth_client_id: str | None = Field(default=None, alias="GITHUB_OAUTH_CLIENT_ID")
    github_oauth_client_secret: str | None = Field(
        default=None,
        alias="GITHUB_OAUTH_CLIENT_SECRET",
    )
    oauth_redirect_base_url: str = Field(
        default="http://localhost:8000",
        alias="OAUTH_REDIRECT_BASE_URL",
    )

    # Email (SMTP optional — logs in dev when unset)
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@tradeflow.ai", alias="SMTP_FROM_EMAIL")

    # Notification integrations (optional)
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")

    # Stripe billing (optional — dev mode when unset)
    stripe_secret_key: str | None = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_publishable_key: str | None = Field(default=None, alias="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_trial_days_default: int = Field(default=14, alias="STRIPE_TRIAL_DAYS_DEFAULT")
    stripe_tax_enabled: bool = Field(default=True, alias="STRIPE_TAX_ENABLED")

    # Rate limiting / brute force
    auth_rate_limit_per_minute: int = Field(default=20, alias="AUTH_RATE_LIMIT_PER_MINUTE")
    login_max_attempts: int = Field(default=5, alias="LOGIN_MAX_ATTEMPTS")
    login_lockout_seconds: int = Field(default=900, alias="LOGIN_LOCKOUT_SECONDS")

    # Avatar uploads
    avatar_upload_dir: str = Field(default="uploads/avatars", alias="AVATAR_UPLOAD_DIR")
    avatar_max_bytes: int = Field(default=2_097_152, alias="AVATAR_MAX_BYTES")

    # Journal screenshot uploads
    journal_upload_dir: str = Field(default="uploads/journal", alias="JOURNAL_UPLOAD_DIR")
    journal_max_bytes: int = Field(default=5_242_880, alias="JOURNAL_MAX_BYTES")

    # Broker integrations
    broker_retry_max_attempts: int = Field(default=3, alias="BROKER_RETRY_MAX_ATTEMPTS")
    broker_health_check_interval_seconds: float = Field(
        default=30.0,
        alias="BROKER_HEALTH_CHECK_INTERVAL_SECONDS",
    )

    # Copy engine
    copy_retry_max_attempts: int = Field(default=5, alias="COPY_RETRY_MAX_ATTEMPTS")
    copy_health_check_interval_seconds: float = Field(
        default=15.0,
        alias="COPY_HEALTH_CHECK_INTERVAL_SECONDS",
    )
    copy_max_parallel_followers: int = Field(default=10, alias="COPY_MAX_PARALLEL_FOLLOWERS")

    # Risk engine
    risk_monitor_interval_seconds: float = Field(
        default=30.0,
        alias="RISK_MONITOR_INTERVAL_SECONDS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def billing_success_url(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/dashboard/billing?checkout=success"

    @property
    def billing_cancel_url(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/dashboard/billing?checkout=canceled"

    @property
    def trusted_hosts(self) -> list[str]:
        if not self.api_trusted_hosts.strip():
            return []
        return [host.strip() for host in self.api_trusted_hosts.split(",") if host.strip()]

    @model_validator(mode="after")
    def enforce_production_defaults(self) -> Self:
        if self.is_production:
            if not self.auth_cookie_secure:
                object.__setattr__(self, "auth_cookie_secure", True)
            if self.api_log_format.lower() != "json":
                object.__setattr__(self, "api_log_format", "json")
        return self

    @field_validator("api_secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            msg = "API_SECRET_KEY must be at least 32 characters"
            raise ValueError(msg)
        return value


def get_settings() -> Settings:
    return Settings()
