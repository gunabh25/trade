from __future__ import annotations

from authlib.integrations.httpx_client import AsyncOAuth2Client

from tradeflow.core.config import Settings
from tradeflow.core.errors import AppError, ErrorCode
from tradeflow.db.enums import OAuthProvider


class OAuthService:
    """Google and GitHub OAuth2 authorization code flow."""

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USERINFO_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_authorization_url(self, provider: OAuthProvider, state: str) -> str:
        redirect_uri = self._redirect_uri(provider)
        if provider == OAuthProvider.GOOGLE:
            client_id = self._settings.google_oauth_client_id
            if not client_id:
                raise AppError(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    "Google OAuth is not configured",
                    status_code=503,
                )
            client = AsyncOAuth2Client(client_id=client_id, redirect_uri=redirect_uri)
            url, _ = client.create_authorization_url(
                self.GOOGLE_AUTH_URL,
                scope="openid email profile",
                state=state,
                access_type="offline",
                prompt="consent",
            )
            return str(url)

        if provider == OAuthProvider.GITHUB:
            client_id = self._settings.github_oauth_client_id
            if not client_id:
                raise AppError(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    "GitHub OAuth is not configured",
                    status_code=503,
                )
            client = AsyncOAuth2Client(client_id=client_id, redirect_uri=redirect_uri)
            url, _ = client.create_authorization_url(
                self.GITHUB_AUTH_URL,
                scope="read:user user:email",
                state=state,
            )
            return str(url)

        raise AppError(ErrorCode.VALIDATION_ERROR, f"Unsupported provider: {provider}")

    async def exchange_code(
        self,
        provider: OAuthProvider,
        code: str,
    ) -> dict[str, str | None]:
        redirect_uri = self._redirect_uri(provider)
        if provider == OAuthProvider.GOOGLE:
            client_id = self._settings.google_oauth_client_id
            client_secret = self._settings.google_oauth_client_secret
            if not client_id or not client_secret:
                raise AppError(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    "Google OAuth is not configured",
                    status_code=503,
                )
            async with AsyncOAuth2Client(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            ) as client:
                token = await client.fetch_token(self.GOOGLE_TOKEN_URL, code=code)
                client.token = token
                resp = await client.get(self.GOOGLE_USERINFO_URL)
                resp.raise_for_status()
                profile = resp.json()
                return {
                    "provider_account_id": profile["sub"],
                    "email": profile.get("email"),
                    "access_token": token.get("access_token"),
                    "refresh_token": token.get("refresh_token"),
                }

        if provider == OAuthProvider.GITHUB:
            client_id = self._settings.github_oauth_client_id
            client_secret = self._settings.github_oauth_client_secret
            if not client_id or not client_secret:
                raise AppError(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    "GitHub OAuth is not configured",
                    status_code=503,
                )
            async with AsyncOAuth2Client(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            ) as client:
                token = await client.fetch_token(self.GITHUB_TOKEN_URL, code=code)
                client.token = token
                user_resp = await client.get(self.GITHUB_USERINFO_URL)
                user_resp.raise_for_status()
                profile = user_resp.json()
                email = profile.get("email")
                if not email:
                    emails_resp = await client.get(self.GITHUB_EMAILS_URL)
                    emails_resp.raise_for_status()
                    for entry in emails_resp.json():
                        if entry.get("primary") and entry.get("verified"):
                            email = entry.get("email")
                            break
                return {
                    "provider_account_id": str(profile["id"]),
                    "email": email,
                    "access_token": token.get("access_token"),
                    "refresh_token": token.get("refresh_token"),
                }

        raise AppError(ErrorCode.VALIDATION_ERROR, f"Unsupported provider: {provider}")

    def _redirect_uri(self, provider: OAuthProvider) -> str:
        base = self._settings.oauth_redirect_base_url.rstrip("/")
        return f"{base}/api/v1/auth/oauth/{provider.value}/callback"
