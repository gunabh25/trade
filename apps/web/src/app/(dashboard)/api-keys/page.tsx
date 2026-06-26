'use client';

import { useEffect, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';
import type { ApiKeyCreated, ApiKeyInfo } from '@tradeflow/types/api';

import * as authApi from '@/features/auth/api/auth-api';

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [name, setName] = useState('');
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);

  async function load() {
    setKeys(await authApi.listApiKeys());
  }

  useEffect(() => {
    void load();
  }, []);

  async function createKey() {
    const created = await authApi.createApiKey(name);
    setCreatedKey(created);
    setName('');
    await load();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">API keys</h1>
      <Card>
        <CardHeader>
          <CardTitle>Create key</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <input
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2"
            placeholder="Key name"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
            }}
          />
          <Button onClick={() => void createKey()} disabled={!name}>
            Create
          </Button>
        </CardContent>
      </Card>
      {createdKey ? (
        <Card>
          <CardContent className="pt-6 text-sm text-amber-300">
            Copy this key now — it will not be shown again: <code>{createdKey.rawKey}</code>
          </CardContent>
        </Card>
      ) : null}
      <Card>
        <CardContent className="divide-y divide-zinc-800 pt-6">
          {keys.map((key) => (
            <div key={key.id} className="flex items-center justify-between py-4 text-sm">
              <div>
                <p>{key.name}</p>
                <p className="text-zinc-500">{key.keyPrefix}…</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void authApi.revokeApiKey(key.id).then(load)}
              >
                Revoke
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </main>
  );
}
