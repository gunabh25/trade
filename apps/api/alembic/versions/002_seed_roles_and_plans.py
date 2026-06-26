"""Seed default roles and subscription plans."""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_seed_roles_and_plans"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE_IDS = {
    "admin": uuid.UUID("00000000-0000-4000-8000-000000000001"),
    "trader": uuid.UUID("00000000-0000-4000-8000-000000000002"),
    "support": uuid.UUID("00000000-0000-4000-8000-000000000003"),
}

PLAN_IDS = {
    "starter": uuid.UUID("00000000-0000-4000-8000-000000000010"),
    "pro": uuid.UUID("00000000-0000-4000-8000-000000000011"),
    "scale": uuid.UUID("00000000-0000-4000-8000-000000000012"),
}


def upgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(
        roles,
        [
            {
                "id": ROLE_IDS["admin"],
                "name": "admin",
                "description": "Full platform administration",
            },
            {
                "id": ROLE_IDS["trader"],
                "name": "trader",
                "description": "Standard trading user",
            },
            {
                "id": ROLE_IDS["support"],
                "name": "support",
                "description": "Read-only support access",
            },
        ],
    )

    plans = sa.table(
        "plans",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("price_cents", sa.Integer()),
        sa.column("currency", sa.String()),
        sa.column("interval", sa.String()),
        sa.column("max_trading_accounts", sa.Integer()),
        sa.column("max_broker_connections", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        plans,
        [
            {
                "id": PLAN_IDS["starter"],
                "code": "starter",
                "name": "Starter",
                "description": "1 leader, up to 10 follower accounts",
                "price_cents": 3900,
                "currency": "USD",
                "interval": "month",
                "max_trading_accounts": 11,
                "max_broker_connections": 5,
                "is_active": True,
            },
            {
                "id": PLAN_IDS["pro"],
                "code": "pro",
                "name": "Pro",
                "description": "Expanded account limits and integrations",
                "price_cents": 7900,
                "currency": "USD",
                "interval": "month",
                "max_trading_accounts": 31,
                "max_broker_connections": 10,
                "is_active": True,
            },
            {
                "id": PLAN_IDS["scale"],
                "code": "scale",
                "name": "Scale",
                "description": "Unlimited followers and API access",
                "price_cents": 12900,
                "currency": "USD",
                "interval": "month",
                "max_trading_accounts": 100,
                "max_broker_connections": 25,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM plans WHERE code IN ('starter', 'pro', 'scale')")
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'trader', 'support')")
