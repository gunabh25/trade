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
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._verify_aud = settings.is_production

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
            "iss": self._issuer,
            "aud": self._audience,
        }
        if session_id:
            payload["sid"] = str(session_id)
        if roles:
            payload["roles"] = roles
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        decode_options: dict[str, bool | list[str]] = {"require": ["sub", "exp", "type"]}
        if self._verify_aud:
            decode_options["require"] = ["sub", "exp", "type", "iss", "aud"]
        payload = jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
            audience=self._audience if self._verify_aud else None,
            issuer=self._issuer if self._verify_aud else None,
            options={
                **decode_options,
                "verify_aud": self._verify_aud,
                "verify_iss": self._verify_aud,
            },
        )
        if payload.get("type") != "access":
            msg = "Invalid token type"
            raise jwt.InvalidTokenError(msg)
        return payload
