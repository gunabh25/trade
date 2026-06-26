from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tradeflow.core.container import Container
from tradeflow.core.errors import UnauthorizedError
from tradeflow.core.security.cookies import get_access_token_from_request
from tradeflow.db.models.user import User
from tradeflow.features.auth.service import AuthService


@inject
async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession] = Depends(
        Provide[Container.db_session_factory],
    ),
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


class CurrentUserContext:
    def __init__(self, user: User, session_id: UUID | None) -> None:
        self.user = user
        self.session_id = session_id


@inject
async def get_current_user_context(
    request: Request,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> CurrentUserContext:
    settings = request.app.state.container.config()
    token = get_access_token_from_request(request, settings)
    if not token:
        raise UnauthorizedError()
    user, session_id = await auth_service.get_user_from_access_token(db, token)
    return CurrentUserContext(user=user, session_id=session_id)


CurrentUser = Annotated[CurrentUserContext, Depends(get_current_user_context)]
