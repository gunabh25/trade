'use client';

import Link from 'next/link';
import { useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Reset password</CardTitle>
        </CardHeader>
        <CardContent>
          {sent ? (
            <p className="text-sm text-zinc-300">
              If an account exists for that email, a reset link has been sent.
            </p>
          ) : (
            <form
              className="space-y-4"
              onSubmit={(event) => {
                void handleSubmit(event);
              }}
            >
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
              {error ? <p className="text-sm text-red-400">{error}</p> : null}
              <Button className="w-full" type="submit">
                Send reset link
              </Button>
            </form>
          )}
          <Link className="mt-4 inline-block text-sm text-blue-400 hover:underline" href="/login">
            Back to sign in
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
