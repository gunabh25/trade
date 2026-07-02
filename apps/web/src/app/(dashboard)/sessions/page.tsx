'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardContent } from '@tradeflow/ui';
import type { SessionInfo } from '@tradeflow/types/api';

import * as authApi from '@/features/auth/api/auth-api';
import { ApiClientError } from '@/lib/errors';

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setSessions(await authApi.listSessions());
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const otherSessions = sessions.filter((session) => !session.isCurrent);

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-4 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Active sessions</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Devices where you are signed in to TradeFlow.
          </p>
        </div>
        {otherSessions.length > 0 ? (
          <Button
            variant="outline"
            onClick={() =>
              void authApi
                .revokeOtherSessions()
                .then(load)
                .catch((err: unknown) => {
                  setError(
                    err instanceof ApiClientError ? err.message : 'Failed to revoke sessions',
                  );
                })
            }
          >
            Sign out all other devices
          </Button>
        ) : null}
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <Card>
        <CardContent className="divide-border divide-y pt-6">
          {loading ? (
            <p className="text-muted-foreground py-4 text-sm">Loading sessions…</p>
          ) : sessions.length === 0 ? (
            <p className="text-muted-foreground py-4 text-sm">No active sessions.</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between gap-4 py-4 text-sm"
              >
                <div>
                  <p>{session.userAgent ?? 'Unknown device'}</p>
                  <p className="text-muted-foreground">
                    {session.ipAddress ?? 'Unknown IP'} ·{' '}
                    {session.isCurrent ? 'Current session' : 'Other device'}
                  </p>
                </div>
                {!session.isCurrent ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void authApi.revokeSession(session.id).then(load)}
                  >
                    Revoke
                  </Button>
                ) : null}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </main>
  );
}
