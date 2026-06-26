'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token') ?? '';
  const [message, setMessage] = useState('Verifying email…');

  useEffect(() => {
    if (!token) {
      setMessage('Missing verification token.');
      return;
    }
    authApi
      .verifyEmail(token)
      .then(() => {
        setMessage('Email verified. Redirecting to dashboard…');
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      })
      .catch(() => {
        setMessage('Verification failed or link expired.');
      });
  }, [token, router]);

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Email verification</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-zinc-300">{message}</p>
        </CardContent>
      </Card>
    </main>
  );
}
