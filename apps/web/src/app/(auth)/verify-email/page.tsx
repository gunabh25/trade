'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import { AuthThemeBar } from '@/components/auth-theme-bar';
import * as authApi from '@/features/auth/api/auth-api';
import { useAuth } from '@/features/auth/components/auth-provider';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refresh } = useAuth();
  const token = searchParams.get('token') ?? '';
  const [message, setMessage] = useState('Verifying email…');

  useEffect(() => {
    if (!token) {
      setMessage('Missing verification token.');
      return;
    }
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    authApi
      .verifyEmail(token)
      .then(async () => {
        if (cancelled) {
          return;
        }
        await refresh();
        setMessage('Email verified. Redirecting to dashboard…');
        timeoutId = setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      })
      .catch(() => {
        if (!cancelled) {
          setMessage('Verification failed or link expired.');
        }
      });

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [token, router, refresh]);

  return (
    <main className="bg-background relative flex min-h-screen items-center justify-center p-6">
      <AuthThemeBar />
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Email verification</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-foreground/90 text-sm">{message}</p>
        </CardContent>
      </Card>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center p-6">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Email verification</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/90 text-sm">Verifying email…</p>
            </CardContent>
          </Card>
        </main>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
