"""Enhance trading journal with emotions, screenshots, strategies, and search indexes."""

from collections.abc import Sequence

from alembic import op

revision: str = "006_journal_enhancements"
down_revision: str | None = "005_risk_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
ALTER TABLE strategies
ADD COLUMN color VARCHAR(7) DEFAULT '#22c55e',
ADD COLUMN rules TEXT
""")
    op.execute("""
ALTER TABLE trade_journals
ADD COLUMN strategy_id UUID REFERENCES strategies (id) ON DELETE SET NULL,
ADD COLUMN notes TEXT,
ADD COLUMN emotions JSONB,
ADD COLUMN mistakes JSONB,
ADD COLUMN lessons_learned TEXT,
ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'manual',
ADD COLUMN symbol VARCHAR(50),
ADD COLUMN side VARCHAR(10),
ADD COLUMN quantity INTEGER,
ADD COLUMN entry_price NUMERIC(18, 8),
ADD COLUMN exit_price NUMERIC(18, 8)
""")
    op.execute("""
CREATE INDEX ix_trade_journals_user_id_symbol
ON trade_journals (user_id, symbol)
""")
    op.execute("""
CREATE INDEX ix_trade_journals_strategy_id ON trade_journals (strategy_id)
""")
    op.execute("""
CREATE INDEX ix_trade_journals_trade_id ON trade_journals (trade_id)
""")

    op.execute("""
CREATE TABLE journal_screenshots (
    id UUID NOT NULL,
    journal_id UUID NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    caption VARCHAR(255),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(journal_id) REFERENCES trade_journals (id) ON DELETE CASCADE
)
""")
    op.execute("""
CREATE INDEX ix_journal_screenshots_journal_id
ON journal_screenshots (journal_id)
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS journal_screenshots")
    op.execute("DROP INDEX IF EXISTS ix_trade_journals_trade_id")
    op.execute("DROP INDEX IF EXISTS ix_trade_journals_strategy_id")
    op.execute("DROP INDEX IF EXISTS ix_trade_journals_user_id_symbol")
    op.execute("""
ALTER TABLE trade_journals
DROP COLUMN IF EXISTS strategy_id,
DROP COLUMN IF EXISTS notes,
DROP COLUMN IF EXISTS emotions,
DROP COLUMN IF EXISTS mistakes,
DROP COLUMN IF EXISTS lessons_learned,
DROP COLUMN IF EXISTS source,
DROP COLUMN IF EXISTS symbol,
DROP COLUMN IF EXISTS side,
DROP COLUMN IF EXISTS quantity,
DROP COLUMN IF EXISTS entry_price,
DROP COLUMN IF EXISTS exit_price
""")
    op.execute("""
ALTER TABLE strategies
DROP COLUMN IF EXISTS color,
DROP COLUMN IF EXISTS rules
""")
