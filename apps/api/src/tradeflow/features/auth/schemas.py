from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isdigit() for char in value):
            msg = "Password must contain at least one digit"
            raise ValueError(msg)
        if not any(char.isalpha() for char in value):
            msg = "Password must contain at least one letter"
            raise ValueError(msg)
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TwoFactorConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    timezone: str | None = Field(default=None, max_length=50)


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    backup_codes: list[str]


class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=8)


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str | None
    last_name: str | None
    bio: str | None
    timezone: str | None
    avatar_url: str | None
    email_verified: bool
    two_factor_enabled: bool
    roles: list[str]
    created_at: datetime


class AuthTokensResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str
    user: UserProfileResponse


class TwoFactorChallengeResponse(BaseModel):
    requires_two_factor: bool = True
    challenge_token: str


class SessionResponse(BaseModel):
    id: UUID
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
    is_current: bool


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str] | None
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str


class MessageResponse(BaseModel):
    message: str
