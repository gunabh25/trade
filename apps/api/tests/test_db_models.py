"""Smoke tests for SQLAlchemy model metadata."""

from tradeflow.db import models  # noqa: F401
from tradeflow.db.base import Base

EXPECTED_TABLES = {
    "users",
    "roles",
    "user_roles",
    "sessions",
    "oauth_accounts",
    "broker_connections",
    "trading_accounts",
    "orders",
    "trades",
    "positions",
    "trade_journals",
    "notes",
    "strategies",
    "risk_rules",
    "notifications",
    "plans",
    "subscriptions",
    "billing_events",
    "audit_logs",
    "api_keys",
    "refresh_tokens",
    "verification_tokens",
}


def test_all_models_registered() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert table_names == EXPECTED_TABLES


def test_uuid_primary_keys() -> None:
    for table in Base.metadata.sorted_tables:
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1
        assert pk_cols[0].name == "id"


def test_soft_delete_tables_have_deleted_at() -> None:
    no_soft_delete = {
        "roles",
        "user_roles",
        "sessions",
        "oauth_accounts",
        "audit_logs",
        "billing_events",
        "verification_tokens",
        "refresh_tokens",
    }
    soft_delete_tables = EXPECTED_TABLES - no_soft_delete
    for name in soft_delete_tables:
        assert "deleted_at" in Base.metadata.tables[name].c


def test_audit_logs_append_only() -> None:
    audit = Base.metadata.tables["audit_logs"]
    assert "deleted_at" not in audit.c
    assert "updated_at" not in audit.c
