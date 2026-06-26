"""Journal production — trade grading."""

from collections.abc import Sequence

from alembic import op

revision: str = "010_journal_production"
down_revision: str | None = "009_admin_portal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
ALTER TABLE trade_journals
ADD COLUMN grade INTEGER CHECK (grade >= 1 AND grade <= 5)
""")
    op.execute("""
CREATE INDEX ix_trade_journals_user_id_grade
ON trade_journals (user_id, grade)
WHERE grade IS NOT NULL
""")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_trade_journals_user_id_grade")
    op.execute("ALTER TABLE trade_journals DROP COLUMN IF EXISTS grade")
