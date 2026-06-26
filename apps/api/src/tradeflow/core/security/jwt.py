from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from tradeflow.core.config import Settings


class JwtService:
    """Signs and verifies short-lived JWT access tokens."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.api_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    def create_access_token(
        self,
        user_id: UUID,
        *,
        session_id: UUID | None = None,
        roles: list[str] | None = None,
    ) -> str:
        now = datetime.now(tz=UTC)
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + self._access_ttl,
            "type": "access",
        }
        if session_id:
            payload["sid"] = str(session_id)
        if roles:
            payload["roles"] = roles
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        payload = jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "access":
            msg = "Invalid token type"
            raise jwt.InvalidTokenError(msg)
        return payload
