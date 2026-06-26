"""Add auth tables and user profile / 2FA columns."""

from collections.abc import Sequence

from alembic import op

revision: str = "003_auth_system"
down_revision: str | None = "002_seed_roles_and_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
ALTER TABLE users
ADD COLUMN avatar_url VARCHAR(500),
ADD COLUMN bio TEXT,
ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN totp_secret_encrypted TEXT,
ADD COLUMN backup_codes_encrypted TEXT
""")
    op.execute("""
CREATE TABLE refresh_tokens (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_id UUID,
    family_id UUID NOT NULL,
    token_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    replaced_by_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY(replaced_by_id) REFERENCES refresh_tokens (id) ON DELETE SET NULL,
    UNIQUE (token_hash)
)
""")
    op.execute("""
CREATE INDEX ix_refresh_tokens_user_id_revoked_at
ON refresh_tokens (user_id, revoked_at)
""")
    op.execute("""
CREATE INDEX ix_refresh_tokens_family_id
ON refresh_tokens (family_id)
""")
    op.execute("""
CREATE TABLE verification_tokens (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    token_type VARCHAR(30) NOT NULL,
    token_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (token_hash)
)
""")
    op.execute("""
CREATE INDEX ix_verification_tokens_user_id_type
ON verification_tokens (user_id, token_type)
""")


def downgrade() -> None:
    op.drop_table("verification_tokens")
    op.drop_table("refresh_tokens")
    op.execute("""
ALTER TABLE users
DROP COLUMN avatar_url,
DROP COLUMN bio,
DROP COLUMN timezone,
DROP COLUMN two_factor_enabled,
DROP COLUMN totp_secret_encrypted,
DROP COLUMN backup_codes_encrypted
""")
