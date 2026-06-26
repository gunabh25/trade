export interface UserProfile {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  bio: string | null;
  timezone: string | null;
  avatarUrl: string | null;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
  roles: string[];
  createdAt: string;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  csrfToken: string;
  user: UserProfile;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TwoFactorChallenge {
  requiresTwoFactor: true;
  challengeToken: string;
}

export interface SessionInfo {
  id: string;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
  expiresAt: string;
  isCurrent: boolean;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  keyPrefix: string;
  scopes: string[] | null;
  lastUsedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
}

export interface ApiKeyCreated extends ApiKeyInfo {
  rawKey: string;
}

export interface MessageResponse {
  message: string;
}

export interface TwoFactorSetup {
  secret: string;
  provisioningUri: string;
  backupCodes: string[];
}

export interface UpdateProfileRequest {
  firstName?: string | null;
  lastName?: string | null;
  bio?: string | null;
  timezone?: string | null;
}
