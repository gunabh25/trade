from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from tradeflow.core.config import Settings
from tradeflow.core.security.jwt import JwtService


@pytest.fixture
def jwt_service() -> JwtService:
    settings = Settings(
        API_SECRET_KEY="test-secret-key-minimum-thirty-two-characters-long",
        DATABASE_URL="postgresql+asyncpg://tradeflow:tradeflow_dev_password@localhost:5432/tradeflow",
        DATABASE_URL_SYNC="postgresql+psycopg://tradeflow:tradeflow_dev_password@localhost:5432/tradeflow",
        REDIS_URL="redis://localhost:6379/0",
        CELERY_BROKER_URL="redis://localhost:6379/1",
        CELERY_RESULT_BACKEND="redis://localhost:6379/2",
    )
    return JwtService(settings)


def test_create_and_decode_access_token(jwt_service: JwtService) -> None:
    user_id = uuid4()
    session_id = uuid4()
    token = jwt_service.create_access_token(user_id, session_id=session_id, roles=["trader"])
    payload = jwt_service.decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["sid"] == str(session_id)
    assert payload["roles"] == ["trader"]


def test_expired_token_rejected(jwt_service: JwtService) -> None:
    settings = jwt_service._secret
    expired = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "exp": datetime.now(tz=UTC) - timedelta(minutes=1),
        },
        settings,
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        jwt_service.decode_access_token(expired)
