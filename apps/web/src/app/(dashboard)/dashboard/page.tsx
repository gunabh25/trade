'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import { useAuth } from '@/features/auth/components/auth-provider';

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return <main className="p-8">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <Button variant="outline" onClick={() => void logout()}>
          Sign out
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Welcome, {user.firstName ?? user.email}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          <p>Email: {user.email}</p>
          <p>Verified: {user.emailVerified ? 'Yes' : 'No'}</p>
          <p>2FA: {user.twoFactorEnabled ? 'Enabled' : 'Disabled'}</p>
          <div className="flex gap-4 pt-2">
            <Link className="text-blue-400 hover:underline" href="/profile">
              Profile & security
            </Link>
            <Link className="text-blue-400 hover:underline" href="/sessions">
              Sessions
            </Link>
            <Link className="text-blue-400 hover:underline" href="/api-keys">
              API keys
            </Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
