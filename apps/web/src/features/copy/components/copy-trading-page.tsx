'use client';

import { Copy, Pause, Play, Plus } from 'lucide-react';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import type { CopyGroup } from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@tradeflow/ui';

import * as copyApi from '@/features/copy/api/copy-api';
import { CreateCopyGroupSheet } from '@/features/copy/components/create-copy-group-sheet';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';
import { ApiClientError } from '@/lib/errors';

interface CopyTradingPageContentProps {
  autoOpenCreate?: boolean;
}

export function CopyTradingPageContent({ autoOpenCreate = false }: CopyTradingPageContentProps) {
  const [groups, setGroups] = useState<CopyGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(autoOpenCreate);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setGroups(await copyApi.listCopyGroups());
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load copy groups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function toggleCopying(group: CopyGroup) {
    setActionId(group.id);
    setError(null);
    try {
      if (group.copying_enabled) {
        await copyApi.stopCopyGroup(group.id);
      } else {
        await copyApi.startCopyGroup(group.id);
      }
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to update copy group');
    } finally {
      setActionId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center p-6">
        <div className="border-muted border-t-foreground h-8 w-8 animate-spin rounded-full border-2" />
      </div>
    );
  }

  return (
    <FadeInStagger className="space-y-6 p-4 sm:p-6">
      <FadeInItem className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Copy Trading</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Mirror a leader account to followers with configurable sizing rules.
          </p>
        </div>
        <Button
          onClick={() => {
            setCreateOpen(true);
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          New copy group
        </Button>
      </FadeInItem>

      {error ? (
        <FadeInItem>
          <Card className="border-red-500/30">
            <CardContent className="pt-6">
              <p className="text-sm text-red-400">{error}</p>
            </CardContent>
          </Card>
        </FadeInItem>
      ) : null}

      <FadeInItem>
        {groups.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <EmptyState
                icon={Copy}
                title="No copy groups yet"
                description="Link at least two trading accounts, then create a group with a leader and followers."
                action={
                  <div className="flex flex-wrap justify-center gap-2">
                    <Button size="sm" variant="outline" asChild>
                      <Link href="/dashboard/accounts?connect=1">Connect accounts</Link>
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        setCreateOpen(true);
                      }}
                    >
                      Create copy group
                    </Button>
                  </div>
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {groups.map((group) => (
              <Card key={group.id}>
                <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
                  <div>
                    <CardTitle className="text-base">{group.name}</CardTitle>
                    <CardDescription>
                      {group.mode} · {group.status} · {group.followers.length} follower
                      {group.followers.length === 1 ? '' : 's'}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={group.copying_enabled ? 'default' : 'outline'}>
                      {group.copying_enabled ? 'Copying' : 'Paused'}
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionId === group.id || group.followers.length === 0}
                      onClick={() => void toggleCopying(group)}
                    >
                      {group.copying_enabled ? (
                        <>
                          <Pause className="mr-1 h-3.5 w-3.5" />
                          Stop
                        </>
                      ) : (
                        <>
                          <Play className="mr-1 h-3.5 w-3.5" />
                          Start
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {group.followers.map((follower) => (
                    <div
                      key={follower.id}
                      className="text-muted-foreground flex flex-wrap justify-between gap-2 text-sm"
                    >
                      <span>Follower · {follower.copy_mode.replaceAll('_', ' ')}</span>
                      <span>
                        Size {follower.sizing_value} · {follower.status}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </FadeInItem>

      <CreateCopyGroupSheet
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={() => void load()}
      />
    </FadeInStagger>
  );
}
