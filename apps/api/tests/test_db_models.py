"""Smoke tests for SQLAlchemy model metadata."""

from tradeflow.db import models  # noqa: F401
from tradeflow.db.base import Base

REQUIRED_TABLES = {
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
    "copy_groups",
    "copy_group_followers",
    "organizations",
    "organization_members",
    "notification_deliveries",
}

COMPOSITE_PK_TABLES: set[str] = set()
NON_ID_PK_TABLES = {"notification_user_settings"}
NO_SOFT_DELETE_TABLES = {
    "roles",
    "user_roles",
    "sessions",
    "oauth_accounts",
    "audit_logs",
    "billing_events",
    "verification_tokens",
    "refresh_tokens",
    "copy_events",
    "execution_logs",
    "order_mappings",
    "risk_breaches",
    "risk_monitor_snapshots",
    "notification_deliveries",
    "notification_digest_queue",
    "notification_user_settings",
    "notification_channel_settings",
    "notification_preferences",
    "system_log_entries",
    "feature_flags",
    "invoices",
    "usage_records",
    "organization_members",
    "journal_screenshots",
    "ai_conversations",
    "ai_messages",
    "ai_insights",
}


def test_all_required_models_registered() -> None:
    table_names = set(Base.metadata.tables.keys())
    missing = REQUIRED_TABLES - table_names
    assert not missing, f"Missing tables: {sorted(missing)}"


def test_uuid_primary_keys() -> None:
    for table in Base.metadata.sorted_tables:
        if table.name in COMPOSITE_PK_TABLES or table.name in NON_ID_PK_TABLES:
            continue
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1
        assert pk_cols[0].name == "id"


def test_soft_delete_tables_have_deleted_at() -> None:
    for table in Base.metadata.sorted_tables:
        if table.name in NO_SOFT_DELETE_TABLES:
            continue
        assert "deleted_at" in table.c, f"{table.name} missing deleted_at"


def test_audit_logs_append_only() -> None:
    audit = Base.metadata.tables["audit_logs"]
    assert "deleted_at" not in audit.c
    assert "updated_at" not in audit.c
