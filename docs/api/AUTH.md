# TradeFlow AI — Authentication API

Base path: `/api/v1/auth`

Interactive docs: `GET /api/docs` (OpenAPI / Swagger)

## Overview

| Mechanism     | Details                                                                             |
| ------------- | ----------------------------------------------------------------------------------- |
| Access token  | JWT (HS256), 15 min default, `Authorization: Bearer` or `tf_access` httpOnly cookie |
| Refresh token | Opaque rotating token, 7 days, `tf_refresh` httpOnly cookie                         |
| CSRF          | Double-submit: `tf_csrf` cookie + `X-CSRF-Token` header on mutating requests        |
| Passwords     | bcrypt cost factor 12                                                               |
| 2FA           | TOTP (Google Authenticator) + backup codes                                          |
| OAuth         | Google, GitHub (authorization code flow)                                            |

## Endpoints

### Registration & login

| Method | Path         | Auth           | Description                                           |
| ------ | ------------ | -------------- | ----------------------------------------------------- |
| POST   | `/register`  | No             | Create account, send verification email               |
| POST   | `/login`     | No             | Email/password login; returns tokens or 2FA challenge |
| POST   | `/login/2fa` | No             | Complete login with TOTP/backup code                  |
| POST   | `/refresh`   | Refresh cookie | Rotate refresh token, issue new access JWT            |
| POST   | `/logout`    | Yes + CSRF     | Revoke session & clear cookies                        |

### Email & password recovery

| Method | Path                   | Description                              |
| ------ | ---------------------- | ---------------------------------------- |
| POST   | `/verify-email`        | Confirm email with token from email link |
| POST   | `/resend-verification` | Resend verification (authenticated)      |
| POST   | `/forgot-password`     | Send password reset email                |
| POST   | `/reset-password`      | Set new password with reset token        |

### OAuth

| Method | Path                     | Description                                        |
| ------ | ------------------------ | -------------------------------------------------- |
| GET    | `/oauth/google`          | Redirect to Google consent                         |
| GET    | `/oauth/google/callback` | Handle callback, set cookies, redirect to frontend |
| GET    | `/oauth/github`          | Redirect to GitHub consent                         |
| GET    | `/oauth/github/callback` | Handle callback                                    |

### Profile

| Method | Path         | Description                         |
| ------ | ------------ | ----------------------------------- |
| GET    | `/me`        | Current user profile                |
| PATCH  | `/me`        | Update name, bio, timezone          |
| POST   | `/me/avatar` | Upload avatar (multipart, max 2 MB) |
| DELETE | `/me/avatar` | Remove avatar                       |

### Two-factor authentication

| Method | Path           | Description                            |
| ------ | -------------- | -------------------------------------- |
| POST   | `/2fa/setup`   | Generate TOTP secret + backup codes    |
| POST   | `/2fa/verify`  | Confirm setup with authenticator code  |
| POST   | `/2fa/disable` | Disable 2FA (password + code required) |

### Sessions & API keys

| Method | Path             | Description                            |
| ------ | ---------------- | -------------------------------------- |
| GET    | `/sessions`      | List active sessions                   |
| DELETE | `/sessions/{id}` | Revoke a session                       |
| DELETE | `/sessions`      | Revoke all other sessions              |
| GET    | `/api-keys`      | List API keys                          |
| POST   | `/api-keys`      | Create API key (raw key returned once) |
| DELETE | `/api-keys/{id}` | Revoke API key                         |

## Security controls

- **Rate limiting** — Redis sliding window on register/login/forgot-password (20 req/min/IP)
- **Brute force protection** — 5 failed logins → 15 min lockout per email
- **Refresh rotation** — Each refresh revokes prior token; reuse revokes entire token family
- **Secure cookies** — `HttpOnly`, `SameSite=Lax`, `Secure` in production (`AUTH_COOKIE_SECURE=true`)

## Environment variables

See `.env.example` for `JWT_*`, `GOOGLE_OAUTH_*`, `GITHUB_OAUTH_*`, `SMTP_*`, `FRONTEND_URL`.

## Database

Migration `003_auth_system` adds:

- `refresh_tokens` — rotating refresh tokens with family ID
- `verification_tokens` — email verification, password reset, 2FA login challenges
- User columns: `avatar_url`, `bio`, `timezone`, `two_factor_enabled`, encrypted TOTP/backup codes
