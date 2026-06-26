'use client';

import type {
  ApiKeyCreated,
  ApiKeyInfo,
  AuthTokens,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  SessionInfo,
  TwoFactorChallenge,
  TwoFactorSetup,
  UpdateProfileRequest,
  UserProfile,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';

function mapUser(raw: Record<string, unknown>): UserProfile {
  return {
    id: String(raw.id),
    email: String(raw.email),
    firstName: (raw.first_name as string | null) ?? null,
    lastName: (raw.last_name as string | null) ?? null,
    bio: (raw.bio as string | null) ?? null,
    timezone: (raw.timezone as string | null) ?? null,
    avatarUrl: (raw.avatar_url as string | null) ?? null,
    emailVerified: Boolean(raw.email_verified),
    twoFactorEnabled: Boolean(raw.two_factor_enabled),
    roles: Array.isArray(raw.roles) ? raw.roles.map(String) : [],
    createdAt: String(raw.created_at),
  };
}

function mapAuthTokens(raw: Record<string, unknown>): AuthTokens {
  return {
    accessToken: String(raw.access_token),
    tokenType: typeof raw.token_type === 'string' ? raw.token_type : 'bearer',
    expiresIn: Number(raw.expires_in),
    csrfToken: String(raw.csrf_token),
    user: mapUser(raw.user as Record<string, unknown>),
  };
}

export async function register(payload: RegisterRequest): Promise<UserProfile> {
  const response = await apiRequest<Record<string, unknown>>('/auth/register', {
    method: 'POST',
    body: {
      email: payload.email,
      password: payload.password,
      first_name: payload.firstName,
      last_name: payload.lastName,
    },
  });
  return mapUser(response.data);
}

export async function login(payload: LoginRequest): Promise<AuthTokens | TwoFactorChallenge> {
  const response = await apiRequest<Record<string, unknown>>('/auth/login', {
    method: 'POST',
    body: payload,
  });
  const data = response.data;
  if (data.requires_two_factor) {
    return {
      requiresTwoFactor: true,
      challengeToken: String(data.challenge_token),
    };
  }
  return mapAuthTokens(data);
}

export async function verifyTwoFactorLogin(
  challengeToken: string,
  code: string,
): Promise<AuthTokens> {
  const response = await apiRequest<Record<string, unknown>>('/auth/login/2fa', {
    method: 'POST',
    body: { challenge_token: challengeToken, code },
  });
  return mapAuthTokens(response.data);
}

export async function logout(): Promise<void> {
  await apiRequest<MessageResponse>('/auth/logout', { method: 'POST' });
}

export async function refreshSession(): Promise<AuthTokens> {
  const response = await apiRequest<Record<string, unknown>>('/auth/refresh', {
    method: 'POST',
    body: {},
  });
  return mapAuthTokens(response.data);
}

export async function getProfile(): Promise<UserProfile> {
  const response = await apiRequest<Record<string, unknown>>('/auth/me');
  return mapUser(response.data);
}

export async function updateProfile(payload: UpdateProfileRequest): Promise<UserProfile> {
  const response = await apiRequest<Record<string, unknown>>('/auth/me', {
    method: 'PATCH',
    body: {
      first_name: payload.firstName,
      last_name: payload.lastName,
      bio: payload.bio,
      timezone: payload.timezone,
    },
  });
  return mapUser(response.data);
}

export async function forgotPassword(email: string): Promise<void> {
  await apiRequest<MessageResponse>('/auth/forgot-password', {
    method: 'POST',
    body: { email },
  });
}

export async function resetPassword(token: string, password: string): Promise<void> {
  await apiRequest<MessageResponse>('/auth/reset-password', {
    method: 'POST',
    body: { token, password },
  });
}

export async function verifyEmail(token: string): Promise<UserProfile> {
  const response = await apiRequest<Record<string, unknown>>('/auth/verify-email', {
    method: 'POST',
    body: { token },
  });
  return mapUser(response.data);
}

export async function listSessions(): Promise<SessionInfo[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/auth/sessions');
  return response.data.map((session) => ({
    id: String(session.id),
    ipAddress: (session.ip_address as string | null) ?? null,
    userAgent: (session.user_agent as string | null) ?? null,
    createdAt: String(session.created_at),
    expiresAt: String(session.expires_at),
    isCurrent: Boolean(session.is_current),
  }));
}

export async function revokeSession(sessionId: string): Promise<void> {
  await apiRequest<MessageResponse>(`/auth/sessions/${sessionId}`, { method: 'DELETE' });
}

export async function setupTwoFactor(): Promise<TwoFactorSetup> {
  const response = await apiRequest<Record<string, unknown>>('/auth/2fa/setup', {
    method: 'POST',
    body: {},
  });
  return {
    secret: String(response.data.secret),
    provisioningUri: String(response.data.provisioning_uri),
    backupCodes: Array.isArray(response.data.backup_codes)
      ? response.data.backup_codes.map(String)
      : [],
  };
}

export async function confirmTwoFactor(code: string): Promise<UserProfile> {
  const response = await apiRequest<Record<string, unknown>>('/auth/2fa/verify', {
    method: 'POST',
    body: { code },
  });
  return mapUser(response.data);
}

export async function listApiKeys(): Promise<ApiKeyInfo[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/auth/api-keys');
  return response.data.map((key) => ({
    id: String(key.id),
    name: String(key.name),
    keyPrefix: String(key.key_prefix),
    scopes: (key.scopes as string[] | null) ?? null,
    lastUsedAt: (key.last_used_at as string | null) ?? null,
    expiresAt: (key.expires_at as string | null) ?? null,
    createdAt: String(key.created_at),
  }));
}

export async function createApiKey(name: string, scopes: string[] = []): Promise<ApiKeyCreated> {
  const response = await apiRequest<Record<string, unknown>>('/auth/api-keys', {
    method: 'POST',
    body: { name, scopes },
  });
  return {
    id: String(response.data.id),
    name: String(response.data.name),
    keyPrefix: String(response.data.key_prefix),
    scopes: (response.data.scopes as string[] | null) ?? null,
    lastUsedAt: (response.data.last_used_at as string | null) ?? null,
    expiresAt: (response.data.expires_at as string | null) ?? null,
    createdAt: String(response.data.created_at),
    rawKey: String(response.data.raw_key),
  };
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await apiRequest<MessageResponse>(`/auth/api-keys/${keyId}`, { method: 'DELETE' });
}
