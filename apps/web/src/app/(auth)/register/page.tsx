'use client';

import { cn } from '@tradeflow/ui';
import { Check, Eye, EyeOff, Lock, Mail, User } from 'lucide-react';
import Link from 'next/link';
import { type SyntheticEvent, useMemo, useState } from 'react';

import { AuthThemeBar } from '@/components/auth-theme-bar';
import { AuthMarketingPanel } from '@/features/auth/components/auth-marketing-panel';

import * as authApi from '@/features/auth/api/auth-api';

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

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!acceptedTerms) {
      setError('Please accept the Terms of Service and Risk Disclosure to continue.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ email, password, firstName, lastName });
      window.location.assign('/login?registered=1');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-background relative flex min-h-screen">
      <AuthThemeBar />
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 sm:px-12">
        <div className="flex w-full max-w-[420px] flex-col">
          <div className="mb-10">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500">
                <span className="text-sm font-bold text-white">T</span>
              </div>
              <span className="text-foreground text-lg font-semibold tracking-tight">
                TradeFlow
              </span>
            </div>
            <p className="text-muted-foreground mt-1 text-[10px] font-medium uppercase tracking-[0.2em]">
              Institutional Grade Trade Copying
            </p>
          </div>

          <div className="mb-8">
            <h1 className="text-foreground text-3xl font-semibold tracking-tight">
              Request Access
            </h1>
            <p className="text-muted-foreground mt-2 text-sm">
              Create your account to access the trading command center.
            </p>
          </div>

          <form
            className="space-y-5"
            onSubmit={(event) => {
              void handleSubmit(event);
            }}
          >
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <label htmlFor="first-name" className="text-foreground/90 text-sm font-medium">
                  First Name
                </label>
                <div className="relative">
                  <User className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                  <input
                    id="first-name"
                    value={firstName}
                    onChange={(e) => {
                      setFirstName(e.target.value);
                    }}
                    className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    placeholder="John"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="last-name" className="text-foreground/90 text-sm font-medium">
                  Last Name
                </label>
                <div className="relative">
                  <User className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                  <input
                    id="last-name"
                    value={lastName}
                    onChange={(e) => {
                      setLastName(e.target.value);
                    }}
                    className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    placeholder="Doe"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="text-foreground/90 text-sm font-medium">
                Work Email
              </label>
              <div className="relative">
                <Mail className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                  required
                  placeholder="name@company.com"
                  className="border-input bg-background text-foreground placeholder:text-muted-foreground h-12 w-full rounded-lg border pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-foreground/90 text-sm font-medium">
                Password
              </label>
              <div className="relative">
                <Lock className="text-muted-foreground absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                  required
                  minLength={8}
                  placeholder="••••••••"
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

            {error ? (
              <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {error}
              </p>
            ) : null}

            <label className="text-muted-foreground flex items-start gap-2.5 text-xs leading-relaxed">
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(e) => {
                  setAcceptedTerms(e.target.checked);
                }}
                className="border-border mt-0.5 rounded"
                required
              />
              <span>
                I agree to the{' '}
                <Link href="/terms" className="text-indigo-400 hover:text-indigo-300">
                  Terms of Service
                </Link>
                ,{' '}
                <Link href="/privacy" className="text-indigo-400 hover:text-indigo-300">
                  Privacy Policy
                </Link>
                , and{' '}
                <Link href="/risk-disclosure" className="text-indigo-400 hover:text-indigo-300">
                  Risk Disclosure
                </Link>
                .
              </span>
            </label>

            <button
              type="submit"
              disabled={loading || !acceptedTerms}
              className="group flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-500 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:brightness-110 disabled:opacity-60"
            >
              {loading ? 'Creating account…' : 'Request Access'}
              {!loading ? (
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              ) : null}
            </button>
          </form>

          <p className="text-muted-foreground mt-8 text-center text-sm">
            Already have an account?{' '}
            <Link
              className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
              href="/login"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
      <div className="hidden w-[45%] max-w-xl lg:block xl:max-w-2xl">
        <AuthMarketingPanel />
      </div>
    </div>
  );
}
