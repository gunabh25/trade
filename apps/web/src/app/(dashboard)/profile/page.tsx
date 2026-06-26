'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';
import { useAuth } from '@/features/auth/components/auth-provider';

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [bio, setBio] = useState('');
  const [totpSetup, setTotpSetup] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState('');

  useEffect(() => {
    if (user) {
      setFirstName(user.firstName ?? '');
      setLastName(user.lastName ?? '');
      setBio(user.bio ?? '');
    }
  }, [user]);

  if (!user) {
    return null;
  }

  async function saveProfile() {
    await authApi.updateProfile({ firstName, lastName, bio });
    await refresh();
  }

  async function startTwoFactor() {
    const setup = await authApi.setupTwoFactor();
    setTotpSetup(setup.provisioningUri);
  }

  async function confirmTwoFactor() {
    await authApi.confirmTwoFactor(totpCode);
    setTotpSetup(null);
    setTotpCode('');
    await refresh();
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Profile & security</h1>
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
            placeholder="First name"
            value={firstName}
            onChange={(e) => {
              setFirstName(e.target.value);
            }}
          />
          <input
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
            placeholder="Last name"
            value={lastName}
            onChange={(e) => {
              setLastName(e.target.value);
            }}
          />
          <textarea
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
            placeholder="Bio"
            value={bio}
            onChange={(e) => {
              setBio(e.target.value);
            }}
          />
          <Button onClick={() => void saveProfile()}>Save profile</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Two-factor authentication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-zinc-400">
            Status: {user.twoFactorEnabled ? 'Enabled' : 'Disabled'}
          </p>
          {!user.twoFactorEnabled ? (
            <>
              <Button variant="outline" onClick={() => void startTwoFactor()}>
                Set up 2FA
              </Button>
              {totpSetup ? (
                <>
                  <p className="break-all text-xs text-zinc-400">{totpSetup}</p>
                  <input
                    className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
                    placeholder="6-digit code"
                    value={totpCode}
                    onChange={(e) => {
                      setTotpCode(e.target.value);
                    }}
                  />
                  <Button onClick={() => void confirmTwoFactor()}>Confirm 2FA</Button>
                </>
              ) : null}
            </>
          ) : null}
        </CardContent>
      </Card>
    </main>
  );
}
