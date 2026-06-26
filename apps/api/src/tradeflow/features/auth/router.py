from __future__ import annotations

import secrets
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import RedirectResponse

from tradeflow.core.container import Container
from tradeflow.core.dependencies.auth import CurrentUser, DbSession
from tradeflow.core.responses import SuccessResponse, success
from tradeflow.core.security.cookies import (
    clear_auth_cookies,
    get_refresh_token_from_request,
    set_auth_cookies,
    validate_csrf,
)
from tradeflow.db.enums import OAuthProvider
from tradeflow.features.auth.oauth_service import OAuthService
from tradeflow.features.auth.schemas import (
    ApiKeyCreatedResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    AuthTokensResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    TwoFactorChallengeResponse,
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    VerifyEmailRequest,
)
from tradeflow.features.auth.service import AuthService, LoginSuccess

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post(
    "/register",
    response_model=SuccessResponse[UserProfileResponse],
    summary="Register a new account",
)
@inject
async def register(
    request: Request,
    payload: RegisterRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    await auth_service.check_rate_limit(f"register:{_client_ip(request)}")
    user = await auth_service.register(
        db,
        payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    request_id = getattr(request.state, "request_id", None)
    return success(user, request_id=request_id)


@router.post(
    "/login",
    response_model=SuccessResponse[AuthTokensResponse | TwoFactorChallengeResponse],
    summary="Login with email and password",
)
@inject
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[AuthTokensResponse | TwoFactorChallengeResponse]:
    await auth_service.check_rate_limit(f"login:{_client_ip(request)}")
    result = await auth_service.login(
        db,
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    request_id = getattr(request.state, "request_id", None)
    if isinstance(result, LoginSuccess):
        settings = request.app.state.container.config()
        set_auth_cookies(
            response,
            settings,
            access_token=result.bundle.access_token,
            refresh_token=result.bundle.refresh_token,
            csrf_token=result.bundle.csrf_token,
        )
        return success(
            AuthTokensResponse(
                access_token=result.bundle.access_token,
                expires_in=result.bundle.expires_in,
                csrf_token=result.bundle.csrf_token,
                user=result.user,
            ),
            request_id=request_id,
        )
    return success(result, request_id=request_id)


@router.post(
    "/login/2fa",
    response_model=SuccessResponse[AuthTokensResponse],
    summary="Complete login with two-factor code",
)
@inject
async def login_two_factor(
    request: Request,
    response: Response,
    payload: TwoFactorVerifyRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[AuthTokensResponse]:
    result = await auth_service.verify_two_factor_login(
        db,
        challenge_token=payload.challenge_token,
        code=payload.code,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    settings = request.app.state.container.config()
    set_auth_cookies(
        response,
        settings,
        access_token=result.bundle.access_token,
        refresh_token=result.bundle.refresh_token,
        csrf_token=result.bundle.csrf_token,
    )
    request_id = getattr(request.state, "request_id", None)
    return success(
        AuthTokensResponse(
            access_token=result.bundle.access_token,
            expires_in=result.bundle.expires_in,
            csrf_token=result.bundle.csrf_token,
            user=result.user,
        ),
        request_id=request_id,
    )


@router.post(
    "/refresh", response_model=SuccessResponse[AuthTokensResponse], summary="Refresh tokens"
)
@inject
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshTokenRequest | None = None,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[AuthTokensResponse]:
    settings = request.app.state.container.config()
    raw_refresh = (
        payload.refresh_token
        if payload and payload.refresh_token
        else get_refresh_token_from_request(request, settings)
    )
    if not raw_refresh:
        from tradeflow.core.errors import UnauthorizedError

        raise UnauthorizedError("Refresh token required")

    bundle = await auth_service.refresh_tokens(
        db,
        refresh_token=raw_refresh,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    set_auth_cookies(
        response,
        settings,
        access_token=bundle.access_token,
        refresh_token=bundle.refresh_token,
        csrf_token=bundle.csrf_token,
    )
    user = await auth_service.get_user_from_access_token(db, bundle.access_token)
    profile = await auth_service.get_profile(db, user[0].id)
    tokens = AuthTokensResponse(
        access_token=bundle.access_token,
        expires_in=bundle.expires_in,
        csrf_token=bundle.csrf_token,
        user=profile,
    )
    request_id = getattr(request.state, "request_id", None)
    return success(tokens, request_id=request_id)


@router.post("/logout", response_model=SuccessResponse[MessageResponse], summary="Logout")
@inject
async def logout(
    request: Request,
    response: Response,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    validate_csrf(request, request.app.state.container.config())
    settings = request.app.state.container.config()
    await auth_service.logout(
        db,
        user_id=current.user.id,
        session_id=current.session_id,
        refresh_token=get_refresh_token_from_request(request, settings),
    )
    clear_auth_cookies(response, settings)
    request_id = getattr(request.state, "request_id", None)
    return success(MessageResponse(message="Logged out"), request_id=request_id)


@router.post("/verify-email", response_model=SuccessResponse[UserProfileResponse])
@inject
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    user = await auth_service.verify_email(db, payload.token)
    request_id = getattr(request.state, "request_id", None)
    return success(user, request_id=request_id)


@router.post("/resend-verification", response_model=SuccessResponse[MessageResponse])
@inject
async def resend_verification(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    validate_csrf(request, request.app.state.container.config())
    await auth_service.resend_verification(db, current.user.id)
    request_id = getattr(request.state, "request_id", None)
    return success(
        MessageResponse(message="Verification email sent"),
        request_id=request_id,
    )


@router.post("/forgot-password", response_model=SuccessResponse[MessageResponse])
@inject
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    await auth_service.check_rate_limit(f"forgot:{payload.email.lower()}")
    await auth_service.forgot_password(db, payload.email)
    request_id = getattr(request.state, "request_id", None)
    return success(
        MessageResponse(message="If the email exists, a reset link was sent"),
        request_id=request_id,
    )


@router.post("/reset-password", response_model=SuccessResponse[MessageResponse])
@inject
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: DbSession,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    await auth_service.reset_password(db, payload.token, payload.password)
    request_id = getattr(request.state, "request_id", None)
    return success(MessageResponse(message="Password updated"), request_id=request_id)


@router.get("/oauth/{provider}", summary="Start OAuth flow")
@inject
async def oauth_start(
    provider: OAuthProvider,
    oauth_service: OAuthService = Depends(Provide[Container.oauth_service]),
) -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    url = oauth_service.get_authorization_url(provider, state)
    response = RedirectResponse(url=url)
    response.set_cookie("oauth_state", state, httponly=True, max_age=600, samesite="lax")
    return response


@router.get("/oauth/{provider}/callback", summary="OAuth callback")
@inject
async def oauth_callback(
    provider: OAuthProvider,
    request: Request,
    response: Response,
    db: DbSession,
    code: str,
    state: str | None = None,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> RedirectResponse:
    cookie_state = request.cookies.get("oauth_state")
    if not state or state != cookie_state:
        from tradeflow.core.errors import ForbiddenError

        raise ForbiddenError("Invalid OAuth state")
    bundle = await auth_service.oauth_callback(
        db,
        provider,
        code,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    settings = request.app.state.container.config()
    redirect = RedirectResponse(url=f"{settings.frontend_url}/dashboard")
    set_auth_cookies(
        redirect,
        settings,
        access_token=bundle.access_token,
        refresh_token=bundle.refresh_token,
        csrf_token=bundle.csrf_token,
    )
    redirect.delete_cookie("oauth_state")
    return redirect


@router.get("/me", response_model=SuccessResponse[UserProfileResponse])
@inject
async def get_me(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    profile = await auth_service.get_profile(db, current.user.id)
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.patch("/me", response_model=SuccessResponse[UserProfileResponse])
@inject
async def update_me(
    request: Request,
    payload: UpdateProfileRequest,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    validate_csrf(request, request.app.state.container.config())
    profile = await auth_service.update_profile(db, current.user.id, payload)
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.post("/me/avatar", response_model=SuccessResponse[UserProfileResponse])
@inject
async def upload_avatar(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    file: UploadFile = File(...),
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    validate_csrf(request, request.app.state.container.config())
    content = await file.read()
    profile = await auth_service.upload_avatar(
        db,
        current.user.id,
        filename=file.filename or "avatar.jpg",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.delete("/me/avatar", response_model=SuccessResponse[UserProfileResponse])
@inject
async def delete_avatar(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    validate_csrf(request, request.app.state.container.config())
    profile = await auth_service.delete_avatar(db, current.user.id)
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.post("/2fa/setup", response_model=SuccessResponse[TwoFactorSetupResponse])
@inject
async def setup_2fa(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[TwoFactorSetupResponse]:
    validate_csrf(request, request.app.state.container.config())
    result = await auth_service.setup_two_factor(db, current.user.id)
    request_id = getattr(request.state, "request_id", None)
    return success(result, request_id=request_id)


@router.post("/2fa/verify", response_model=SuccessResponse[UserProfileResponse])
@inject
async def verify_2fa_setup(
    request: Request,
    payload: TwoFactorConfirmRequest,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    validate_csrf(request, request.app.state.container.config())
    profile = await auth_service.confirm_two_factor(db, current.user.id, payload.code)
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.post("/2fa/disable", response_model=SuccessResponse[UserProfileResponse])
@inject
async def disable_2fa(
    request: Request,
    payload: TwoFactorDisableRequest,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[UserProfileResponse]:
    validate_csrf(request, request.app.state.container.config())
    profile = await auth_service.disable_two_factor(
        db,
        current.user.id,
        password=payload.password,
        code=payload.code,
    )
    request_id = getattr(request.state, "request_id", None)
    return success(profile, request_id=request_id)


@router.get("/sessions", response_model=SuccessResponse[list[SessionResponse]])
@inject
async def list_sessions(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[list[SessionResponse]]:
    sessions = await auth_service.list_sessions(
        db,
        current.user.id,
        current_session_id=current.session_id,
    )
    request_id = getattr(request.state, "request_id", None)
    return success(sessions, request_id=request_id)


@router.delete("/sessions/{session_id}", response_model=SuccessResponse[MessageResponse])
@inject
async def revoke_session(
    request: Request,
    session_id: UUID,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    validate_csrf(request, request.app.state.container.config())
    await auth_service.revoke_session(db, current.user.id, session_id)
    request_id = getattr(request.state, "request_id", None)
    return success(MessageResponse(message="Session revoked"), request_id=request_id)


@router.delete("/sessions", response_model=SuccessResponse[MessageResponse])
@inject
async def revoke_other_sessions(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    validate_csrf(request, request.app.state.container.config())
    if not current.session_id:
        from tradeflow.core.errors import ForbiddenError

        raise ForbiddenError("Current session unknown")
    await auth_service.revoke_other_sessions(db, current.user.id, current.session_id)
    request_id = getattr(request.state, "request_id", None)
    return success(MessageResponse(message="Other sessions revoked"), request_id=request_id)


@router.get("/api-keys", response_model=SuccessResponse[list[ApiKeyResponse]])
@inject
async def list_api_keys(
    request: Request,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[list[ApiKeyResponse]]:
    keys = await auth_service.list_api_keys(db, current.user.id)
    request_id = getattr(request.state, "request_id", None)
    return success(keys, request_id=request_id)


@router.post("/api-keys", response_model=SuccessResponse[ApiKeyCreatedResponse])
@inject
async def create_api_key(
    request: Request,
    payload: ApiKeyCreateRequest,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[ApiKeyCreatedResponse]:
    validate_csrf(request, request.app.state.container.config())
    key = await auth_service.create_api_key(db, current.user.id, payload)
    request_id = getattr(request.state, "request_id", None)
    return success(key, request_id=request_id)


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse[MessageResponse])
@inject
async def revoke_api_key(
    request: Request,
    key_id: UUID,
    db: DbSession,
    current: CurrentUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> SuccessResponse[MessageResponse]:
    validate_csrf(request, request.app.state.container.config())
    await auth_service.revoke_api_key(db, current.user.id, key_id)
    request_id = getattr(request.state, "request_id", None)
    return success(MessageResponse(message="API key revoked"), request_id=request_id)
