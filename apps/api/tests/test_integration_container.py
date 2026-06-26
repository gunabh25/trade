"""DI container integration — verify all providers resolve without import errors."""

from __future__ import annotations

import pytest

from tradeflow.core.container import Container


@pytest.fixture
def container() -> Container:
    return Container()


def test_container_resolves_core_infrastructure(container: Container) -> None:
    assert container.config() is not None
    assert container.db_engine() is not None
    assert container.db_session_factory() is not None
    assert container.redis_client() is not None


def test_container_resolves_broker_stack(container: Container) -> None:
    registry = container.broker_adapter_registry()
    assert len(registry.supported_brokers()) >= 1
    assert container.broker_session_manager() is not None
    assert container.connection_monitor() is not None


def test_container_resolves_copy_engine(container: Container) -> None:
    orchestrator = container.copy_orchestrator()
    assert orchestrator is not None
    assert container.trade_mapping_store() is not None
    assert container.copy_retry_queue() is not None
    assert container.copy_trading_service() is not None


def test_container_resolves_risk_engine(container: Container) -> None:
    assert container.risk_evaluator() is not None
    assert container.risk_monitor() is not None
    assert container.risk_service() is not None


def test_container_resolves_feature_services(container: Container) -> None:
    assert container.auth_service() is not None
    assert container.broker_service() is not None
    assert container.journal_service() is not None
    assert container.analytics_service() is not None
    assert container.notification_service() is not None
    assert container.billing_service() is not None
    assert container.admin_service() is not None
    assert container.health_service() is not None


def test_worker_runtime_uses_same_container_graph() -> None:
    from tradeflow.workers.runtime import get_worker_container

    worker = get_worker_container()
    orchestrator = worker.copy_orchestrator()
    monitor = worker.risk_monitor()
    dispatcher = worker.notification_dispatcher()
    assert orchestrator is not None
    assert monitor is not None
    assert dispatcher is not None
