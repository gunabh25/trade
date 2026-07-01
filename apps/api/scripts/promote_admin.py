#!/usr/bin/env python3
"""Grant the admin role to an existing user (production bootstrap).

Usage (local):
  cd apps/api && PYTHONPATH=src python scripts/promote_admin.py --email you@example.com

Usage (Railway):
  railway run --service trade python scripts/promote_admin.py --email you@example.com
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from tradeflow.core.config import get_settings
from tradeflow.db.enums import RoleName
from tradeflow.db.models.user import Role, User, UserRole


def main() -> int:
    parser = argparse.ArgumentParser(description="Grant admin role to a user by email")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument(
        "--verify-email",
        action="store_true",
        help="Also mark the user's email as verified",
    )
    args = parser.parse_args()
    email = args.email.lower().strip()

    settings = get_settings()
    engine = create_engine(str(settings.database_url_sync))

    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
        if user is None:
            print(f"Error: no user found with email {email}", file=sys.stderr)
            print("Register at /register first, then run this script again.", file=sys.stderr)
            return 1

        admin_role = db.scalar(select(Role).where(Role.name == RoleName.ADMIN))
        if admin_role is None:
            print("Error: admin role not found — run database migrations.", file=sys.stderr)
            return 1

        existing = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == admin_role.id,
            ),
        )
        if existing is None:
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            print(f"Granted admin role to {email}")
        else:
            print(f"User {email} already has admin role")

        if args.verify_email and user.email_verified_at is None:
            user.email_verified_at = datetime.now(tz=UTC)
            print(f"Marked {email} as email-verified")

        db.commit()

    print("Done. Log out, log in again at /login, then open /admin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
