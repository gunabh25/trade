'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardContent } from '@tradeflow/ui';
import type { SessionInfo } from '@tradeflow/types/api';

import * as authApi from '@/features/auth/api/auth-api';

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);

  async function load() {
    setSessions(await authApi.listSessions());
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Active sessions</h1>
      <Card>
        <CardContent className="divide-y divide-zinc-800 pt-6">
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center justify-between py-4 text-sm">
              <div>
                <p>{session.userAgent ?? 'Unknown device'}</p>
                <p className="text-zinc-500">
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
          ))}
        </CardContent>
      </Card>
    </main>
  );
}
