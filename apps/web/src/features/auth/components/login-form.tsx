'use client';

import { cn } from '@tradeflow/ui';
import { Check, Eye, EyeOff, Lock, Mail } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useMemo, useState } from 'react';

import * as authApi from '@/features/auth/api/auth-api';
import { useAuth } from '@/features/auth/components/auth-provider';
import { ApiClientError } from '@/lib/errors';
import { getOAuthUrl } from '@/lib/api/client';

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

function getPasswordStrength(password: string): { score: number; label: string } {
  if (!password) return { score: 0, label: 'Enter password' };
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  const normalized = Math.min(4, Math.max(1, Math.ceil(score * 0.8)));
  const labels = ['Weak', 'Fair', 'Good', 'High', 'High'] as const;
  return { score: normalized, label: labels[normalized] ?? 'High' };
}

export function LoginForm() {
  const searchParams = useSearchParams();
  const { refresh } = useAuth();
  const nextPath = searchParams.get('next') ?? '/dashboard';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [challengeToken, setChallengeToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  function navigateAfterLogin() {
    const destination = nextPath.startsWith('/') ? nextPath : '/dashboard';
    // Auth is enforced by middleware via cookies, so use a full navigation
    // after login to avoid racing a client-side route transition.
    window.location.assign(destination);
  }

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (challengeToken) {
        await authApi.verifyTwoFactorLogin(challengeToken, twoFactorCode);
        await refresh();
        navigateAfterLogin();
        return;
      }
      const result = await authApi.login({ email, password });
      if ('requiresTwoFactor' in result) {
        setChallengeToken(result.challengeToken);
        return;
      }
      if (rememberDevice) {
        localStorage.setItem('tf_remember_device', '1');
      }
      await refresh();
      navigateAfterLogin();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Login failed',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex w-full max-w-[420px] flex-col">
      <div className="mb-10">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500">
            <span className="text-sm font-bold text-white">T</span>
          </div>
          <span className="text-foreground text-lg font-semibold tracking-tight">TradeFlow</span>
        </div>
        <p className="text-muted-foreground mt-1 text-[10px] font-medium uppercase tracking-[0.2em]">
          Institutional Grade Trade Copying
        </p>
      </div>

      <div className="mb-8">
        <h1 className="text-foreground text-3xl font-semibold tracking-tight">Welcome Back</h1>
        <p className="text-muted-foreground mt-2 text-sm">Access your trading command center.</p>
        {process.env.NODE_ENV === 'development' ? (
          <p className="border-border bg-muted/40 text-muted-foreground mt-3 rounded-md border px-3 py-2 text-xs">
            Dev login: <span className="text-foreground/90">demo@tradeflow.ai</span> /{' '}
            <span className="text-foreground/90">DemoPass123</span>
          </p>
        ) : null}
      </div>

      {!challengeToken ? (
        <>
          <div className="grid grid-cols-2 gap-3">
            <a
              href={getOAuthUrl('google')}
              className="border-border bg-muted/40 text-foreground/90 hover:bg-muted/60 hover:text-foreground flex h-11 items-center justify-center gap-2 rounded-lg border text-sm font-medium transition-colors"
            >
              <GoogleIcon />
              Google
            </a>
            <a
              href={getOAuthUrl('github')}
              className="border-border bg-muted/40 text-foreground/90 hover:bg-muted/60 hover:text-foreground flex h-11 items-center justify-center gap-2 rounded-lg border text-sm font-medium transition-colors"
            >
              <GitHubIcon />
              GitHub
            </a>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="border-border w-full border-t" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-background text-muted-foreground px-3 text-[10px] font-medium uppercase tracking-widest">
                Or continue with
              </span>
            </div>
          </div>
        </>
      ) : null}

      <form
        className="space-y-5"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
      >
        {!challengeToken ? (
          <>
            <div className="space-y-2">
              <label htmlFor="email" className="text-foreground/90 text-sm font-medium">
                Work Email
              </label>
              <div className="relative">
                <Mail className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                  required
                  className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-foreground/90 text-sm font-medium">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
                >
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                  required
                  className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border pl-10 pr-11 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
                <button
                  type="button"
                  onClick={() => {
                    setShowPassword((v) => !v);
                  }}
                  className="text-muted-foreground hover:text-muted-foreground absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {password.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  <div className="flex gap-1">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div
                        key={i}
                        className={cn(
                          'h-1 flex-1 rounded-full transition-colors',
                          i < passwordStrength.score
                            ? 'bg-gradient-to-r from-indigo-500 to-cyan-400'
                            : 'bg-muted',
                        )}
                      />
                    ))}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                    <Check className="h-3 w-3" />
                    Security level: {passwordStrength.label}
                  </div>
                </div>
              ) : null}
            </div>

            <label className="flex cursor-pointer items-center gap-2.5">
              <input
                type="checkbox"
                checked={rememberDevice}
                onChange={(e) => {
                  setRememberDevice(e.target.checked);
                }}
                className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-indigo-500 focus:ring-indigo-500/50 focus:ring-offset-0"
              />
              <span className="text-muted-foreground text-sm">
                Remember this device for 30 days
              </span>
            </label>
          </>
        ) : (
          <div className="space-y-2">
            <label htmlFor="totp" className="text-foreground/90 text-sm font-medium">
              Authenticator Code
            </label>
            <input
              id="totp"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="000000"
              value={twoFactorCode}
              onChange={(e) => {
                setTwoFactorCode(e.target.value);
              }}
              required
              className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border px-4 text-center text-lg tracking-[0.3em] focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        )}

        {error ? (
          <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="group flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-500 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:brightness-110 disabled:opacity-60"
        >
          {loading ? 'Signing in…' : challengeToken ? 'Verify & Sign In' : 'Sign In to Terminal'}
          {!loading && !challengeToken ? (
            <span className="transition-transform group-hover:translate-x-0.5">→</span>
          ) : null}
        </button>
      </form>

      <p className="text-muted-foreground mt-8 text-center text-sm">
        New to the platform?{' '}
        <Link
          href="/register"
          className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          Request access
        </Link>
      </p>
    </div>
  );
}
