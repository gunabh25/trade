from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import aiofiles  # type: ignore[import-untyped]
import pyotp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tradeflow.core.config import Settings
from tradeflow.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from tradeflow.core.logging import get_logger
from tradeflow.core.security.encryption import EncryptionService
from tradeflow.core.security.jwt import JwtService
from tradeflow.core.security.password import (
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from tradeflow.core.security.rate_limit import LoginProtection, RateLimiter, generate_csrf_token
from tradeflow.db.enums import AuditAction, OAuthProvider, RoleName, VerificationTokenType
from tradeflow.db.models.api_key import ApiKey
from tradeflow.db.models.audit import AuditLog
from tradeflow.db.models.auth import RefreshToken, VerificationToken
from tradeflow.db.models.oauth import OAuthAccount
from tradeflow.db.models.session import Session
from tradeflow.db.models.user import Role, User, UserRole
from tradeflow.features.auth.email_service import EmailService
from tradeflow.features.auth.oauth_service import OAuthService
from tradeflow.features.auth.schemas import (
    ApiKeyCreatedResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    RegisterRequest,
    SessionResponse,
    TwoFactorChallengeResponse,
    TwoFactorSetupResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)

logger = get_logger(__name__)


def _role_name_str(name: RoleName | str) -> str:
    return name.value if isinstance(name, RoleName) else str(name)


def _user_role_names(user: User) -> list[str]:
    return [_role_name_str(ur.role.name) for ur in user.user_roles]


@dataclass(frozen=True)
class AuthSessionBundle:
    access_token: str
    refresh_token: str
    csrf_token: str
    session_id: UUID
    expires_in: int


@dataclass(frozen=True)
class LoginSuccess:
    bundle: AuthSessionBundle
    user: UserProfileResponse


class AuthService:
    """Complete authentication, session, profile, and API key management."""

    def __init__(
        self,
        settings: Settings,
        jwt_service: JwtService,
        encryption_service: EncryptionService,
        email_service: EmailService,
        oauth_service: OAuthService,
        rate_limiter: RateLimiter,
        login_protection: LoginProtection,
    ) -> None:
        self._settings = settings
        self._jwt = jwt_service
        self._encryption = encryption_service
        self._email = email_service
        self._oauth = oauth_service
        self._rate_limiter = rate_limiter
        self._login_protection = login_protection

    async def register(
        self,
        db: AsyncSession,
        payload: RegisterRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserProfileResponse:
        existing = await db.scalar(
            select(User).where(User.email == payload.email.lower(), User.deleted_at.is_(None)),
        )
        if existing:
            raise ConflictError("An account with this email already exists")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        trader_role = await db.scalar(select(Role).where(Role.name == RoleName.TRADER))
        if trader_role:
            db.add(UserRole(user_id=user.id, role_id=trader_role.id))

        await self._create_verification_token(db, user.id)
        await db.commit()
        await db.refresh(user, attribute_names=["user_roles"])

        user_with_roles = await self._get_user_with_roles(db, user.id)
        return self._to_profile(user_with_roles)

    async def login(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> LoginSuccess | TwoFactorChallengeResponse:
        email_lower = email.lower()
        locked, retry_after = await self._login_protection.is_locked(email_lower)
        if locked:
            raise ForbiddenError(f"Account temporarily locked. Retry in {retry_after}s")

        user = await db.scalar(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email_lower, User.deleted_at.is_(None)),
        )
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            await self._login_protection.record_failure(email_lower)
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("Account is disabled")

        await self._login_protection.reset(email_lower)

        if user.two_factor_enabled:
            challenge = await self._create_verification_token(
                db,
                user.id,
                token_type=VerificationTokenType.TWO_FACTOR_LOGIN,
                ttl_hours=1,
            )
            await db.commit()
            return TwoFactorChallengeResponse(challenge_token=challenge)

        bundle = await self._issue_session(db, user, ip_address=ip_address, user_agent=user_agent)
        await self._audit(
            db, user.id, AuditAction.LOGIN, ip_address=ip_address, user_agent=user_agent
        )
        await db.commit()
        return LoginSuccess(bundle=bundle, user=self._to_profile(user))

    async def verify_two_factor_login(
        self,
        db: AsyncSession,
        *,
        challenge_token: str,
        code: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> LoginSuccess:
        user = await self._consume_verification_token(
            db,
            challenge_token,
            VerificationTokenType.TWO_FACTOR_LOGIN,
        )
        if not self._verify_totp(user, code) and not self._verify_backup_code(db, user, code):
            raise UnauthorizedError("Invalid two-factor code")

        user = await self._get_user_with_roles(db, user.id)
        bundle = await self._issue_session(db, user, ip_address=ip_address, user_agent=user_agent)
        await self._audit(
            db, user.id, AuditAction.LOGIN, ip_address=ip_address, user_agent=user_agent
        )
        await db.commit()
        return LoginSuccess(bundle=bundle, user=self._to_profile(user))

    async def refresh_tokens(
        self,
        db: AsyncSession,
        *,
        refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthSessionBundle:
        token_hash = hash_token(refresh_token)
        stored = await db.scalar(
            select(RefreshToken)
            .options(
                selectinload(RefreshToken.user)
                .selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            ),
        )
        if not stored or stored.expires_at < datetime.now(tz=UTC):
            raise UnauthorizedError("Invalid or expired refresh token")

        if stored.replaced_by_id is not None:
            await self._revoke_token_family(db, stored.family_id)
            await db.commit()
            raise UnauthorizedError("Refresh token reuse detected")

        user = stored.user
        if not user.is_active or user.deleted_at is not None:
            raise UnauthorizedError("Account is not active")

        new_raw = generate_token()
        new_token = RefreshToken(
            user_id=user.id,
            session_id=stored.session_id,
            family_id=stored.family_id,
            token_hash=hash_token(new_raw),
            expires_at=datetime.now(tz=UTC)
            + timedelta(days=self._settings.jwt_refresh_token_expire_days),
        )
        db.add(new_token)
        await db.flush()
        stored.revoked_at = datetime.now(tz=UTC)
        stored.replaced_by_id = new_token.id

        roles = _user_role_names(user)
        access = self._jwt.create_access_token(
            user.id,
            session_id=stored.session_id,
            roles=roles,
        )
        csrf = generate_csrf_token()
        await db.commit()
        return AuthSessionBundle(
            access_token=access,
            refresh_token=new_raw,
            csrf_token=csrf,
            session_id=stored.session_id or user.id,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
        )

    async def logout(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        session_id: UUID | None,
        refresh_token: str | None,
    ) -> None:
        if refresh_token:
            token_hash = hash_token(refresh_token)
            stored = await db.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash),
            )
            if stored:
                stored.revoked_at = datetime.now(tz=UTC)
                if stored.session_id:
                    session_id = stored.session_id

        if session_id:
            session = await db.get(Session, session_id)
            if session and session.user_id == user_id:
                session.revoked_at = datetime.now(tz=UTC)
                await db.execute(
                    update(RefreshToken)
                    .where(
                        RefreshToken.session_id == session_id,
                        RefreshToken.revoked_at.is_(None),
                    )
                    .values(revoked_at=datetime.now(tz=UTC)),
                )

        await self._audit(db, user_id, AuditAction.LOGOUT)
        await db.commit()

    async def verify_email(self, db: AsyncSession, token: str) -> UserProfileResponse:
        user = await self._consume_verification_token(
            db,
            token,
            VerificationTokenType.EMAIL_VERIFICATION,
        )
        user.email_verified_at = datetime.now(tz=UTC)
        user = await self._get_user_with_roles(db, user.id)
        await db.commit()
        return self._to_profile(user)

    async def resend_verification(self, db: AsyncSession, user_id: UUID) -> None:
        user = await self._get_user_with_roles(db, user_id)
        if user.email_verified_at:
            raise ConflictError("Email is already verified")
        raw = await self._create_verification_token(db, user.id)
        await self._email.send_verification_email(user.email, raw)
        await db.commit()

    async def forgot_password(self, db: AsyncSession, email: str) -> None:
        user = await db.scalar(
            select(User).where(User.email == email.lower(), User.deleted_at.is_(None)),
        )
        if user:
            raw = await self._create_verification_token(
                db,
                user.id,
                token_type=VerificationTokenType.PASSWORD_RESET,
                ttl_hours=1,
            )
            await self._email.send_password_reset_email(user.email, raw)
        await db.commit()

    async def reset_password(self, db: AsyncSession, token: str, password: str) -> None:
        user = await self._consume_verification_token(
            db,
            token,
            VerificationTokenType.PASSWORD_RESET,
        )
        user.password_hash = hash_password(password)
        await db.execute(
            update(Session)
            .where(Session.user_id == user.id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=UTC)),
        )
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=UTC)),
        )
        await db.commit()

    async def get_profile(self, db: AsyncSession, user_id: UUID) -> UserProfileResponse:
        user = await self._get_user_with_roles(db, user_id)
        return self._to_profile(user)

    async def update_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: UpdateProfileRequest,
    ) -> UserProfileResponse:
        user = await self._get_user_with_roles(db, user_id)
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name
        if payload.bio is not None:
            user.bio = payload.bio
        if payload.timezone is not None:
            user.timezone = payload.timezone
        await db.commit()
        await db.refresh(user)
        return self._to_profile(user)

    async def upload_avatar(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> UserProfileResponse:
        if len(content) > self._settings.avatar_max_bytes:
            raise ForbiddenError("Avatar exceeds maximum size")
        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if content_type not in allowed:
            raise ForbiddenError("Unsupported image type")

        ext = Path(filename).suffix.lower() or ".jpg"
        upload_dir = Path(self._settings.avatar_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / f"{user_id}{ext}"

        async with aiofiles.open(dest, "wb") as handle:
            await handle.write(content)

        user = await self._get_user_with_roles(db, user_id)
        user.avatar_url = f"/uploads/avatars/{user_id}{ext}"
        await db.commit()
        return self._to_profile(user)

    async def delete_avatar(self, db: AsyncSession, user_id: UUID) -> UserProfileResponse:
        user = await self._get_user_with_roles(db, user_id)
        if user.avatar_url:
            path = Path(self._settings.avatar_upload_dir) / Path(user.avatar_url).name
            if path.exists():
                path.unlink()
            user.avatar_url = None
        await db.commit()
        return self._to_profile(user)

    async def setup_two_factor(self, db: AsyncSession, user_id: UUID) -> TwoFactorSetupResponse:
        user = await self._get_user_with_roles(db, user_id)
        secret = pyotp.random_base32()
        backup_codes = [secrets.token_hex(4) for _ in range(8)]
        user.totp_secret_encrypted = self._encryption.encrypt(secret)
        user.backup_codes_encrypted = self._encryption.encrypt_json(
            [hash_token(code) for code in backup_codes],
        )
        user.two_factor_enabled = False
        await db.commit()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name="TradeFlow AI")
        return TwoFactorSetupResponse(
            secret=secret, provisioning_uri=uri, backup_codes=backup_codes
        )

    async def confirm_two_factor(
        self,
        db: AsyncSession,
        user_id: UUID,
        code: str,
    ) -> UserProfileResponse:
        user = await self._get_user_with_roles(db, user_id)
        if not user.totp_secret_encrypted:
            raise ConflictError("Two-factor setup has not been started")
        if not self._verify_totp(user, code):
            raise UnauthorizedError("Invalid authenticator code")
        user.two_factor_enabled = True
        await db.commit()
        return self._to_profile(user)

    async def disable_two_factor(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        password: str,
        code: str,
    ) -> UserProfileResponse:
        user = await self._get_user_with_roles(db, user_id)
        if not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid password")
        if not self._verify_totp(user, code):
            raise UnauthorizedError("Invalid authenticator code")
        user.two_factor_enabled = False
        user.totp_secret_encrypted = None
        user.backup_codes_encrypted = None
        await db.commit()
        return self._to_profile(user)

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        current_session_id: UUID | None,
    ) -> list[SessionResponse]:
        result = await db.scalars(
            select(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .order_by(Session.created_at.desc()),
        )
        return [
            SessionResponse(
                id=s.id,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=s.created_at,
                expires_at=s.expires_at,
                is_current=s.id == current_session_id,
            )
            for s in result.all()
        ]

    async def revoke_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        session = await db.get(Session, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Session not found")
        session.revoked_at = datetime.now(tz=UTC)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=UTC)),
        )
        await db.commit()

    async def revoke_other_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_session_id: UUID,
    ) -> None:
        await db.execute(
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.id != current_session_id,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(tz=UTC)),
        )
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.session_id != current_session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(tz=UTC)),
        )
        await db.commit()

    async def list_api_keys(self, db: AsyncSession, user_id: UUID) -> list[ApiKeyResponse]:
        keys = await db.scalars(
            select(ApiKey)
            .where(
                ApiKey.user_id == user_id, ApiKey.deleted_at.is_(None), ApiKey.revoked_at.is_(None)
            )
            .order_by(ApiKey.created_at.desc()),
        )
        return [self._to_api_key(k) for k in keys.all()]

    async def create_api_key(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: ApiKeyCreateRequest,
    ) -> ApiKeyCreatedResponse:
        raw_key = f"tf_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:12]
        api_key = ApiKey(
            user_id=user_id,
            name=payload.name,
            key_prefix=prefix,
            key_hash=hash_token(raw_key),
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        base = self._to_api_key(api_key)
        return ApiKeyCreatedResponse(**base.model_dump(), raw_key=raw_key)

    async def revoke_api_key(self, db: AsyncSession, user_id: UUID, key_id: UUID) -> None:
        api_key = await db.scalar(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
                ApiKey.deleted_at.is_(None),
            ),
        )
        if not api_key:
            raise NotFoundError("API key not found")
        api_key.revoked_at = datetime.now(tz=UTC)
        await db.commit()

    async def oauth_callback(
        self,
        db: AsyncSession,
        provider: OAuthProvider,
        code: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthSessionBundle:
        profile = await self._oauth.exchange_code(provider, code)
        provider_account_id = profile["provider_account_id"]
        if not provider_account_id:
            raise UnauthorizedError("OAuth profile missing account id")

        oauth_account = await db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_account_id == provider_account_id,
            ),
        )
        user: User | None = None
        if oauth_account:
            user = await self._get_user_with_roles(db, oauth_account.user_id)
        else:
            email = profile.get("email")
            if email:
                user = await db.scalar(
                    select(User)
                    .options(selectinload(User.user_roles).selectinload(UserRole.role))
                    .where(User.email == str(email).lower(), User.deleted_at.is_(None)),
                )
            if not user:
                if not email:
                    raise ConflictError("OAuth account has no email; cannot create user")
                user = User(
                    email=str(email).lower(),
                    first_name=None,
                    last_name=None,
                    is_active=True,
                    email_verified_at=datetime.now(tz=UTC),
                )
                db.add(user)
                await db.flush()
                trader_role = await db.scalar(select(Role).where(Role.name == RoleName.TRADER))
                if trader_role:
                    db.add(UserRole(user_id=user.id, role_id=trader_role.id))

            access_enc = (
                self._encryption.encrypt(str(profile["access_token"]))
                if profile.get("access_token")
                else None
            )
            refresh_enc = (
                self._encryption.encrypt(str(profile["refresh_token"]))
                if profile.get("refresh_token")
                else None
            )
            db.add(
                OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_account_id=provider_account_id,
                    access_token_encrypted=access_enc,
                    refresh_token_encrypted=refresh_enc,
                    profile_email=str(profile.get("email")) if profile.get("email") else None,
                ),
            )

        user = await self._get_user_with_roles(db, user.id)
        bundle = await self._issue_session(db, user, ip_address=ip_address, user_agent=user_agent)
        await self._audit(
            db, user.id, AuditAction.LOGIN, ip_address=ip_address, user_agent=user_agent
        )
        await db.commit()
        return bundle

    async def get_user_from_access_token(
        self,
        db: AsyncSession,
        access_token: str,
    ) -> tuple[User, UUID | None]:
        try:
            payload = self._jwt.decode_access_token(access_token)
        except Exception as exc:
            raise UnauthorizedError("Invalid access token") from exc

        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"]) if payload.get("sid") else None
        user = await self._get_user_with_roles(db, user_id)
        if not user.is_active or user.deleted_at is not None:
            raise UnauthorizedError("Account is not active")
        if session_id:
            session = await db.get(Session, session_id)
            if not session or session.revoked_at or session.expires_at < datetime.now(tz=UTC):
                raise UnauthorizedError("Session expired or revoked")
        return user, session_id

    async def check_rate_limit(self, key: str) -> None:
        allowed, retry_after = await self._rate_limiter.check(
            key,
            limit=self._settings.auth_rate_limit_per_minute,
            window_seconds=60,
        )
        if not allowed:
            raise ForbiddenError(f"Rate limit exceeded. Retry in {retry_after}s")

    async def _issue_session(
        self,
        db: AsyncSession,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthSessionBundle:
        session_token = generate_token()
        session = Session(
            user_id=user.id,
            token_hash=hash_token(session_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(tz=UTC)
            + timedelta(days=self._settings.jwt_refresh_token_expire_days),
        )
        db.add(session)
        await db.flush()

        raw_refresh = generate_token()
        family_id = uuid.uuid4()
        refresh = RefreshToken(
            user_id=user.id,
            session_id=session.id,
            family_id=family_id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(tz=UTC)
            + timedelta(days=self._settings.jwt_refresh_token_expire_days),
        )
        db.add(refresh)
        await db.flush()

        roles = _user_role_names(user)
        access = self._jwt.create_access_token(user.id, session_id=session.id, roles=roles)
        csrf = generate_csrf_token()

        if not user.email_verified_at:
            raw_verify = await self._create_verification_token(db, user.id)
            await self._email.send_verification_email(user.email, raw_verify)

        return AuthSessionBundle(
            access_token=access,
            refresh_token=raw_refresh,
            csrf_token=csrf,
            session_id=session.id,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
        )

    async def _create_verification_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        token_type: VerificationTokenType = VerificationTokenType.EMAIL_VERIFICATION,
        ttl_hours: int = 24,
    ) -> str:
        raw = generate_token()
        db.add(
            VerificationToken(
                user_id=user_id,
                token_type=token_type,
                token_hash=hash_token(raw),
                expires_at=datetime.now(tz=UTC) + timedelta(hours=ttl_hours),
                created_at=datetime.now(tz=UTC),
            ),
        )
        if token_type == VerificationTokenType.EMAIL_VERIFICATION:
            user = await db.get(User, user_id)
            if user:
                await self._email.send_verification_email(user.email, raw)
        return raw

    async def _consume_verification_token(
        self,
        db: AsyncSession,
        raw_token: str,
        token_type: VerificationTokenType,
    ) -> User:
        stored = await db.scalar(
            select(VerificationToken).where(
                VerificationToken.token_hash == hash_token(raw_token),
                VerificationToken.token_type == token_type,
                VerificationToken.used_at.is_(None),
            ),
        )
        if not stored or stored.expires_at < datetime.now(tz=UTC):
            raise UnauthorizedError("Invalid or expired token")
        stored.used_at = datetime.now(tz=UTC)
        user = await self._get_user_with_roles(db, stored.user_id)
        return user

    async def _revoke_token_family(self, db: AsyncSession, family_id: UUID) -> None:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=UTC)),
        )

    async def _get_user_with_roles(self, db: AsyncSession, user_id: UUID) -> User:
        user = await db.scalar(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id, User.deleted_at.is_(None)),
        )
        if not user:
            raise NotFoundError("User not found")
        return user

    def _verify_totp(self, user: User, code: str) -> bool:
        if not user.totp_secret_encrypted:
            return False
        secret = self._encryption.decrypt(user.totp_secret_encrypted)
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    def _verify_backup_code(self, db: AsyncSession, user: User, code: str) -> bool:
        if not user.backup_codes_encrypted:
            return False
        hashes: list[str] = self._encryption.decrypt_json(user.backup_codes_encrypted)
        code_hash = hash_token(code.replace("-", "").lower())
        if code_hash in hashes:
            hashes.remove(code_hash)
            user.backup_codes_encrypted = self._encryption.encrypt_json(hashes)
            return True
        return False

    async def _audit(
        self,
        db: AsyncSession,
        user_id: UUID,
        action: AuditAction,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource_type="user",
                resource_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(tz=UTC),
            ),
        )

    def _to_profile(self, user: User) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            bio=user.bio,
            timezone=user.timezone,
            avatar_url=user.avatar_url,
            email_verified=user.email_verified_at is not None,
            two_factor_enabled=user.two_factor_enabled,
            roles=_user_role_names(user),
            created_at=user.created_at,
        )

    def _to_api_key(self, api_key: ApiKey) -> ApiKeyResponse:
        return ApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            scopes=api_key.scopes,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
        )
