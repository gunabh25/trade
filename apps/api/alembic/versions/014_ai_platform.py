"""AI platform tables."""

from collections.abc import Sequence

from alembic import op

revision: str = "014_ai_platform"
down_revision: str | None = "013_production_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_type VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE INDEX ix_ai_conversations_user_id_updated_at
    ON ai_conversations (user_id, updated_at DESC)
""")
    op.execute("""
CREATE INDEX ix_ai_conversations_user_feature
    ON ai_conversations (user_id, feature_type)
""")

    op.execute("""
CREATE TABLE ai_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE INDEX ix_ai_messages_conversation_id_created_at
    ON ai_messages (conversation_id, created_at ASC)
""")

    op.execute("""
CREATE TABLE ai_insights (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_type VARCHAR(50) NOT NULL,
    template_id VARCHAR(100) NOT NULL,
    context_hash VARCHAR(64) NOT NULL,
    input_summary TEXT,
    output TEXT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
    op.execute("""
CREATE INDEX ix_ai_insights_user_feature ON ai_insights (user_id, feature_type)
""")
    op.execute("""
CREATE INDEX ix_ai_insights_context_hash ON ai_insights (context_hash)
""")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_insights")
    op.execute("DROP TABLE IF EXISTS ai_messages")
    op.execute("DROP TABLE IF EXISTS ai_conversations")
