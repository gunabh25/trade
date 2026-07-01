'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { type SyntheticEvent, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ email, password, firstName, lastName });
      router.push('/login?registered=1');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
        </CardHeader>
        <CardContent>
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
                minLength={8}
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block space-y-1 text-sm">
                <span>First name</span>
                <input
                  className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(e.target.value);
                  }}
                />
              </label>
              <label className="block space-y-1 text-sm">
                <span>Last name</span>
                <input
                  className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                  value={lastName}
                  onChange={(e) => {
                    setLastName(e.target.value);
                  }}
                />
              </label>
            </div>
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button className="w-full" disabled={loading} type="submit">
              {loading ? 'Creating account…' : 'Register'}
            </Button>
          </form>
          <p className="mt-4 text-sm text-zinc-400">
            Already have an account?{' '}
            <Link className="text-blue-400 hover:underline" href="/login">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
