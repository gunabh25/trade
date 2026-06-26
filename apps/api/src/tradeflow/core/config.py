from pydantic import Field, PostgresDsn, RedisDsn, field_validator
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

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_url_sync: PostgresDsn = Field(alias="DATABASE_URL_SYNC")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")

    redis_url: RedisDsn = Field(alias="REDIS_URL")

    celery_broker_url: RedisDsn = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: RedisDsn = Field(alias="CELERY_RESULT_BACKEND")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @field_validator("api_secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            msg = "API_SECRET_KEY must be at least 32 characters"
            raise ValueError(msg)
        return value


def get_settings() -> Settings:
    return Settings()
