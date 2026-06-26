'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@tradeflow/ui';

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
    <div className="mx-auto max-w-2xl space-y-6 p-4 sm:p-6">
      <Card className="border-border/60 bg-card/80 shadow-none">
        <CardHeader>
          <CardTitle className="text-base font-medium">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="First name"
            value={firstName}
            onChange={(e) => {
              setFirstName(e.target.value);
            }}
          />
          <Input
            placeholder="Last name"
            value={lastName}
            onChange={(e) => {
              setLastName(e.target.value);
            }}
          />
          <textarea
            className="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
            placeholder="Bio"
            value={bio}
            onChange={(e) => {
              setBio(e.target.value);
            }}
          />
          <Button onClick={() => void saveProfile()}>Save profile</Button>
        </CardContent>
      </Card>
      <Card className="border-border/60 bg-card/80 shadow-none">
        <CardHeader>
          <CardTitle className="text-base font-medium">Two-factor authentication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-muted-foreground text-sm">
            Status: {user.twoFactorEnabled ? 'Enabled' : 'Disabled'}
          </p>
          {!user.twoFactorEnabled ? (
            <>
              <Button variant="outline" onClick={() => void startTwoFactor()}>
                Set up 2FA
              </Button>
              {totpSetup ? (
                <>
                  <p className="text-muted-foreground break-all text-xs">{totpSetup}</p>
                  <Input
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
    </div>
  );
}
