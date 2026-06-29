from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tradeflow.core.config import Settings, get_settings
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.core.security.jwt import JwtService
from tradeflow.core.security.rate_limit import LoginProtection, RateLimiter
from tradeflow.db.session import create_session_factory
from tradeflow.engine.mapping import TradeMappingStore
from tradeflow.engine.orchestrator import CopyOrchestrator
from tradeflow.engine.retry_queue import RetryQueue
from tradeflow.features.admin.observability import AdminObservabilityService
from tradeflow.features.admin.service import AdminService
from tradeflow.features.analytics.service import AnalyticsService
from tradeflow.features.auth.email_service import EmailService
from tradeflow.features.auth.oauth_service import OAuthService
from tradeflow.features.auth.service import AuthService
from tradeflow.features.billing.entitlements import EntitlementService
from tradeflow.features.billing.service import BillingService
from tradeflow.features.billing.usage_meter import UsageMeter
from tradeflow.features.broker.service import BrokerConnectionService
from tradeflow.features.copy_trading.service import CopyTradingService
from tradeflow.features.health.service import HealthService
from tradeflow.features.journal.service import JournalService
from tradeflow.features.notifications.service import NotificationService
from tradeflow.features.risk.service import RiskService
from tradeflow.integrations.brokers.manager import BrokerSessionManager
from tradeflow.integrations.brokers.monitor import ConnectionMonitor
from tradeflow.integrations.brokers.registry import BrokerAdapterRegistry
from tradeflow.integrations.brokers.retry import RetryPolicy
from tradeflow.integrations.stripe.client import StripeClient
from tradeflow.notifications.dispatcher import NotificationDispatcher
from tradeflow.risk.actions import RiskActionExecutor
from tradeflow.risk.alerts import RiskAlertService
from tradeflow.risk.evaluator import RiskEvaluator
from tradeflow.risk.monitor import RiskMonitor
from tradeflow.risk.state import RiskStateStore


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "tradeflow.api.v1.router",
            "tradeflow.features.health.router",
            "tradeflow.features.auth.router",
            "tradeflow.features.broker.router",
            "tradeflow.features.copy_trading.router",
            "tradeflow.features.risk.router",
            "tradeflow.features.journal.router",
            "tradeflow.features.analytics.router",
            "tradeflow.features.notifications.router",
            "tradeflow.features.billing.router",
            "tradeflow.features.admin.router",
            "tradeflow.core.dependencies.auth",
        ],
    )

    config: providers.Singleton[Settings] = providers.Singleton(get_settings)

    db_engine: providers.Singleton[AsyncEngine] = providers.Singleton(
        create_async_engine,
        providers.Callable(str, config.provided.database_url),
        pool_size=config.provided.database_pool_size,
        max_overflow=config.provided.database_max_overflow,
        pool_timeout=config.provided.database_pool_timeout,
        pool_pre_ping=True,
        echo=config.provided.is_development,
    )

    db_session_factory: providers.Singleton[async_sessionmaker[AsyncSession]] = providers.Singleton(
        create_session_factory, db_engine
    )

    redis_client: providers.Singleton[Redis[Any]] = providers.Singleton(
        Redis.from_url,
        providers.Callable(str, config.provided.redis_url),
        decode_responses=True,
        max_connections=config.provided.redis_max_connections,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
        retry_on_timeout=True,
    )

    health_service: providers.Factory[HealthService] = providers.Factory(
        HealthService,
        settings=config,
        db_engine=db_engine,
        redis_client=redis_client,
    )

    jwt_service: providers.Singleton[JwtService] = providers.Singleton(JwtService, settings=config)
    encryption_service: providers.Singleton[EncryptionService] = providers.Singleton(
        EncryptionService,
        settings=config,
    )
    email_service: providers.Singleton[EmailService] = providers.Singleton(
        EmailService,
        settings=config,
    )
    oauth_service: providers.Singleton[OAuthService] = providers.Singleton(
        OAuthService,
        settings=config,
    )
    rate_limiter: providers.Singleton[RateLimiter] = providers.Singleton(
        RateLimiter,
        redis=redis_client,
    )
    login_protection: providers.Singleton[LoginProtection] = providers.Singleton(
        LoginProtection,
        redis=redis_client,
        max_attempts=config.provided.login_max_attempts,
        lockout_seconds=config.provided.login_lockout_seconds,
    )
    notification_dispatcher: providers.Singleton[NotificationDispatcher] = providers.Singleton(
        NotificationDispatcher,
        settings=config,
        redis=redis_client,
    )

    broker_retry_policy: providers.Singleton[RetryPolicy] = providers.Singleton(
        RetryPolicy,
        max_attempts=config.provided.broker_retry_max_attempts,
    )

    broker_adapter_registry: providers.Singleton[BrokerAdapterRegistry] = providers.Singleton(
        BrokerAdapterRegistry,
        retry_policy=broker_retry_policy,
    )

    connection_monitor: providers.Singleton[ConnectionMonitor] = providers.Singleton(
        ConnectionMonitor,
        health_check_interval_seconds=config.provided.broker_health_check_interval_seconds,
    )

    broker_session_manager: providers.Singleton[BrokerSessionManager] = providers.Singleton(
        BrokerSessionManager,
        registry=broker_adapter_registry,
        monitor=connection_monitor,
        encryption_service=encryption_service,
    )

    stripe_client: providers.Singleton[StripeClient] = providers.Singleton(
        StripeClient,
        settings=config,
    )

    usage_meter: providers.Singleton[UsageMeter] = providers.Singleton(
        UsageMeter,
        redis=redis_client,
    )

    entitlement_service: providers.Factory[EntitlementService] = providers.Factory(
        EntitlementService,
        usage_meter=usage_meter,
    )

    broker_service: providers.Factory[BrokerConnectionService] = providers.Factory(
        BrokerConnectionService,
        registry=broker_adapter_registry,
        session_manager=broker_session_manager,
        encryption_service=encryption_service,
        entitlements=entitlement_service,
    )

    trade_mapping_store: providers.Singleton[TradeMappingStore] = providers.Singleton(
        TradeMappingStore,
        redis=redis_client,
    )

    copy_retry_queue: providers.Singleton[RetryQueue] = providers.Singleton(
        RetryQueue,
        redis=redis_client,
        max_attempts=config.provided.copy_retry_max_attempts,
    )

    risk_state_store: providers.Singleton[RiskStateStore] = providers.Singleton(
        RiskStateStore,
        redis=redis_client,
    )

    risk_evaluator: providers.Singleton[RiskEvaluator] = providers.Singleton(
        RiskEvaluator,
        state_store=risk_state_store,
    )

    copy_orchestrator: providers.Singleton[CopyOrchestrator] = providers.Singleton(
        CopyOrchestrator,
        session_manager=broker_session_manager,
        mapping_store=trade_mapping_store,
        retry_queue=copy_retry_queue,
        max_parallel_followers=config.provided.copy_max_parallel_followers,
        risk_evaluator=risk_evaluator,
        notification_dispatcher=notification_dispatcher,
    )

    risk_action_executor: providers.Singleton[RiskActionExecutor] = providers.Singleton(
        RiskActionExecutor,
        session_manager=broker_session_manager,
        state_store=risk_state_store,
    )

    risk_alert_service: providers.Singleton[RiskAlertService] = providers.Singleton(
        RiskAlertService,
        state_store=risk_state_store,
        notification_dispatcher=notification_dispatcher,
    )

    risk_monitor: providers.Singleton[RiskMonitor] = providers.Singleton(
        RiskMonitor,
        evaluator=risk_evaluator,
        action_executor=risk_action_executor,
        alert_service=risk_alert_service,
        state_store=risk_state_store,
        session_manager=broker_session_manager,
    )

    risk_service: providers.Factory[RiskService] = providers.Factory(
        RiskService,
        evaluator=risk_evaluator,
        monitor=risk_monitor,
        action_executor=risk_action_executor,
        alert_service=risk_alert_service,
        state_store=risk_state_store,
    )

    journal_service: providers.Factory[JournalService] = providers.Factory(JournalService)

    analytics_service: providers.Factory[AnalyticsService] = providers.Factory(AnalyticsService)

    notification_service: providers.Factory[NotificationService] = providers.Factory(
        NotificationService,
    )

    billing_service: providers.Factory[BillingService] = providers.Factory(
        BillingService,
        settings=config,
        stripe_client=stripe_client,
        entitlements=entitlement_service,
        notification_dispatcher=notification_dispatcher,
    )

    auth_service: providers.Factory[AuthService] = providers.Factory(
        AuthService,
        settings=config,
        jwt_service=jwt_service,
        encryption_service=encryption_service,
        email_service=email_service,
        oauth_service=oauth_service,
        rate_limiter=rate_limiter,
        login_protection=login_protection,
        notification_dispatcher=notification_dispatcher,
        billing_service=billing_service,
        entitlements=entitlement_service,
    )

    admin_service: providers.Factory[AdminService] = providers.Factory(
        AdminService,
        settings=config,
        health_service=health_service,
        billing_service=billing_service,
        connection_monitor=connection_monitor,
        broker_service=broker_service,
    )

    admin_observability_service: providers.Factory[AdminObservabilityService] = providers.Factory(
        AdminObservabilityService,
        settings=config,
        redis=redis_client,
        health_service=health_service,
    )

    copy_trading_service: providers.Factory[CopyTradingService] = providers.Factory(
        CopyTradingService,
        orchestrator=copy_orchestrator,
        mapping_store=trade_mapping_store,
        retry_queue=copy_retry_queue,
        entitlements=entitlement_service,
    )


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def generate_request_id() -> str:
    return str(uuid.uuid4())
