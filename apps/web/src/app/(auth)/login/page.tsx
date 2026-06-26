'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';
import { getOAuthUrl } from '@/lib/api/client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [challengeToken, setChallengeToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (challengeToken) {
        await authApi.verifyTwoFactorLogin(challengeToken, twoFactorCode);
        router.push('/dashboard');
        return;
      }
      const result = await authApi.login({ email, password });
      if ('requiresTwoFactor' in result) {
        setChallengeToken(result.challengeToken);
        return;
      }
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to TradeFlow AI</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              void handleSubmit(event);
            }}
          >
            {!challengeToken ? (
              <>
                <label className="block space-y-1 text-sm">
                  <span>Email</span>
                  <input
                    className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                    }}
                    required
                  />
                </label>
                <label className="block space-y-1 text-sm">
                  <span>Password</span>
                  <input
                    className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                    }}
                    required
                  />
                </label>
              </>
            ) : (
              <label className="block space-y-1 text-sm">
                <span>Authenticator code</span>
                <input
                  className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                  value={twoFactorCode}
                  onChange={(e) => {
                    setTwoFactorCode(e.target.value);
                  }}
                  required
                />
              </label>
            )}
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button className="w-full" disabled={loading} type="submit">
              {loading ? 'Signing in…' : challengeToken ? 'Verify code' : 'Sign in'}
            </Button>
          </form>
          <div className="mt-4 flex flex-col gap-2 text-sm">
            <a className="text-blue-400 hover:underline" href={getOAuthUrl('google')}>
              Continue with Google
            </a>
            <a className="text-blue-400 hover:underline" href={getOAuthUrl('github')}>
              Continue with GitHub
            </a>
            <Link className="text-zinc-400 hover:underline" href="/register">
              Create an account
            </Link>
            <Link className="text-zinc-400 hover:underline" href="/forgot-password">
              Forgot password?
            </Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
