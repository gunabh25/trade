'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
      setTimeout(() => {
        router.push('/login');
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reset failed');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Set a new password</CardTitle>
        </CardHeader>
        <CardContent>
          {done ? (
            <p className="text-sm text-green-400">Password updated. Redirecting to sign in…</p>
          ) : (
            <form
              className="space-y-4"
              onSubmit={(event) => {
                void handleSubmit(event);
              }}
            >
              <label className="block space-y-1 text-sm">
                <span>New password</span>
                <input
                  className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                  required
                  minLength={8}
                />
              </label>
              {error ? <p className="text-sm text-red-400">{error}</p> : null}
              <Button className="w-full" type="submit" disabled={!token}>
                Update password
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center p-6">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Set a new password</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-400">Loading…</p>
            </CardContent>
          </Card>
        </main>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}
