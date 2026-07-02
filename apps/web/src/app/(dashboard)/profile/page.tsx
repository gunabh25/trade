'use client';

import { useEffect, useRef, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@tradeflow/ui';

import * as authApi from '@/features/auth/api/auth-api';
import { useAuth } from '@/features/auth/components/auth-provider';
import { resolveAvatarUrl } from '@/lib/avatar-url';
import { ApiClientError } from '@/lib/errors';

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [bio, setBio] = useState('');
  const [totpSetup, setTotpSetup] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

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

  const avatarUrl = resolveAvatarUrl(user.avatarUrl);

  async function saveProfile() {
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      await authApi.updateProfile({ firstName, lastName, bio });
      await refresh();
      setSuccess('Profile saved.');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  async function startTwoFactor() {
    setError(null);
    try {
      const setup = await authApi.setupTwoFactor();
      setTotpSetup(setup.provisioningUri);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to start 2FA setup');
    }
  }

  async function confirmTwoFactor() {
    setError(null);
    try {
      await authApi.confirmTwoFactor(totpCode);
      setTotpSetup(null);
      setTotpCode('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Invalid 2FA code');
    }
  }

  async function disableTwoFactor() {
    setError(null);
    try {
      await authApi.disableTwoFactor(disablePassword, disableCode);
      setDisablePassword('');
      setDisableCode('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to disable 2FA');
    }
  }

  async function handleAvatarChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await authApi.uploadAvatar(file);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to upload avatar');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  }

  async function removeAvatar() {
    setUploading(true);
    setError(null);
    try {
      await authApi.deleteAvatar();
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to remove avatar');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4 sm:p-6">
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      {success ? <p className="text-sm text-green-400">{success}</p> : null}

      <Card className="border-border/60 bg-card/80 shadow-none">
        <CardHeader>
          <CardTitle className="text-base font-medium">Avatar</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-4">
          <div className="bg-muted flex h-16 w-16 items-center justify-center overflow-hidden rounded-full text-lg font-semibold">
            {avatarUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={avatarUrl} alt="" className="h-full w-full object-cover" />
            ) : (
              (user.firstName?.[0] ?? user.email[0] ?? '?').toUpperCase()
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={(event) => void handleAvatarChange(event)}
            />
            <Button
              variant="outline"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? 'Uploading…' : 'Upload photo'}
            </Button>
            {avatarUrl ? (
              <Button variant="ghost" disabled={uploading} onClick={() => void removeAvatar()}>
                Remove
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

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
          <Button type="button" disabled={saving} onClick={() => void saveProfile()}>
            {saving ? 'Saving…' : 'Save profile'}
          </Button>
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
          ) : (
            <div className="border-border space-y-3 border-t pt-3">
              <p className="text-muted-foreground text-sm">
                Enter your password and a current authenticator code to disable 2FA.
              </p>
              <Input
                type="password"
                placeholder="Password"
                value={disablePassword}
                onChange={(e) => {
                  setDisablePassword(e.target.value);
                }}
              />
              <Input
                placeholder="6-digit code"
                value={disableCode}
                onChange={(e) => {
                  setDisableCode(e.target.value);
                }}
              />
              <Button variant="destructive" onClick={() => void disableTwoFactor()}>
                Disable 2FA
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
