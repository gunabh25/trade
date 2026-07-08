'use client';

import { Loader2, Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import type { CopyGroup, TradingAccount } from '@tradeflow/types/api';

import { Button, Input, Sheet, SheetContent, SheetHeader, SheetTitle, cn } from '@tradeflow/ui';

import {
  addCopyFollower,
  createCopyGroup,
  startCopyGroup,
  updateCopyGroup,
} from '@/features/copy/api/copy-api';
import { listTradingAccounts } from '@/features/broker/api/broker-api';
import { ApiClientError } from '@/lib/errors';

const COPY_MODES = [
  { value: 'fixed_quantity', label: 'Fixed quantity', hint: 'Copy a fixed contract size' },
  { value: 'risk_multiplier', label: 'Risk multiplier', hint: 'Multiply leader size (e.g. 2×)' },
  {
    value: 'percentage_allocation',
    label: 'Percentage',
    hint: 'Percent of leader size (e.g. 50%)',
  },
  { value: 'reverse_copy', label: 'Reverse copy', hint: 'Flip buy/sell on follower' },
] as const;

interface FollowerDraft {
  accountId: string;
  copyMode: string;
  sizingValue: string;
}

interface CreateCopyGroupSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
  group?: CopyGroup | null;
}

export function CreateCopyGroupSheet({
  open,
  onOpenChange,
  onCreated,
  group,
}: CreateCopyGroupSheetProps) {
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [name, setName] = useState('My copy group');
  const [mode, setMode] = useState<'live' | 'sim'>('sim');
  const [leaderId, setLeaderId] = useState('');
  const [followers, setFollowers] = useState<FollowerDraft[]>([]);
  const [startAfterCreate, setStartAfterCreate] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isEditing = group != null;

  const followerOptions = useMemo(
    () => accounts.filter((account) => account.id !== leaderId),
    [accounts, leaderId],
  );

  useEffect(() => {
    if (!open) return;
    setError(null);
    setLoadingAccounts(true);
    void listTradingAccounts()
      .then((items) => {
        setAccounts(items);
        setName(group?.name ?? 'My copy group');
        setMode(group?.mode === 'live' ? 'live' : 'sim');
        setLeaderId(group?.leader_account_id ?? items[0]?.id ?? '');
        setFollowers([]);
        setStartAfterCreate(true);
      })
      .catch(() => {
        setError('Failed to load trading accounts');
      })
      .finally(() => {
        setLoadingAccounts(false);
      });
  }, [open, group]);

  function addFollowerRow() {
    const candidate = followerOptions.find(
      (account) => !followers.some((follower) => follower.accountId === account.id),
    );
    if (!candidate) return;
    setFollowers((prev) => [
      ...prev,
      { accountId: candidate.id, copyMode: 'fixed_quantity', sizingValue: '1' },
    ]);
  }

  function updateFollower(index: number, patch: Partial<FollowerDraft>) {
    setFollowers((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function removeFollower(index: number) {
    setFollowers((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!leaderId) {
      setError('Select a leader account.');
      return;
    }
    if (!isEditing && followers.length === 0) {
      setError('Add at least one follower account.');
      return;
    }

    const invalidSizing =
      !isEditing &&
      followers.some((follower) => !follower.sizingValue || Number(follower.sizingValue) <= 0);
    if (invalidSizing) {
      setError('Follower sizing must be greater than zero.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      if (group) {
        await updateCopyGroup(group.id, {
          name: name.trim(),
          leader_account_id: leaderId,
          mode,
        });
        onCreated();
        onOpenChange(false);
        return;
      }

      const createdGroup = await createCopyGroup({
        name: name.trim(),
        leader_account_id: leaderId,
        mode,
      });

      for (const follower of followers) {
        await addCopyFollower(createdGroup.id, {
          follower_account_id: follower.accountId,
          copy_mode: follower.copyMode,
          sizing_value: Number(follower.sizingValue),
        });
      }

      if (startAfterCreate) {
        await startCopyGroup(createdGroup.id);
      }

      onCreated();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to create copy group');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="text-left">
          <SheetTitle>{isEditing ? 'Edit copy group' : 'Create copy group'}</SheetTitle>
        </SheetHeader>

        {loadingAccounts ? (
          <div className="mt-10 flex justify-center">
            <Loader2 className="text-muted-foreground h-6 w-6 animate-spin" />
          </div>
        ) : accounts.length < 2 ? (
          <div className="mt-6 space-y-4">
            <p className="text-muted-foreground text-sm">
              You need at least two linked trading accounts — one leader and one follower. Connect
              two paper brokers (use different account IDs, e.g. paper-leader and paper-follower).
            </p>
            <Button variant="outline" asChild>
              <a href="/dashboard/accounts?connect=1">Connect another account</a>
            </Button>
          </div>
        ) : (
          <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-5">
            <div className="space-y-2">
              <label htmlFor="group-name" className="text-sm font-medium">
                Group name
              </label>
              <Input
                id="group-name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                }}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Mode</label>
              <div className="grid grid-cols-2 gap-2">
                {(['sim', 'live'] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => {
                      setMode(value);
                    }}
                    className={cn(
                      'rounded-lg border px-3 py-2 text-sm capitalize',
                      mode === value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-accent/40',
                    )}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="leader-account" className="text-sm font-medium">
                Leader account
              </label>
              <select
                id="leader-account"
                value={leaderId}
                onChange={(e) => {
                  setLeaderId(e.target.value);
                }}
                className="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
              >
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} ({account.broker})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Followers</p>
                {!isEditing ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={addFollowerRow}
                    disabled={followers.length >= followerOptions.length}
                  >
                    <Plus className="mr-1 h-3.5 w-3.5" />
                    Add follower
                  </Button>
                ) : null}
              </div>

              {isEditing ? (
                <p className="text-muted-foreground text-xs">
                  Editing currently updates the group name, leader account, and mode. Follower
                  changes can still be added through the existing group flow.
                </p>
              ) : followers.length === 0 ? (
                <p className="text-muted-foreground text-xs">
                  Add follower accounts and how their order size should be calculated.
                </p>
              ) : (
                followers.map((follower, index) => (
                  <div
                    key={`${follower.accountId}-${index}`}
                    className="space-y-2 rounded-lg border p-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <select
                        value={follower.accountId}
                        onChange={(e) => {
                          updateFollower(index, { accountId: e.target.value });
                        }}
                        className="border-input bg-background flex-1 rounded-md border px-2 py-1.5 text-sm"
                      >
                        {followerOptions.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.name}
                          </option>
                        ))}
                      </select>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        onClick={() => {
                          removeFollower(index);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={follower.copyMode}
                        onChange={(e) => {
                          updateFollower(index, { copyMode: e.target.value });
                        }}
                        className="border-input bg-background rounded-md border px-2 py-1.5 text-sm"
                      >
                        {COPY_MODES.map((copyMode) => (
                          <option key={copyMode.value} value={copyMode.value}>
                            {copyMode.label}
                          </option>
                        ))}
                      </select>
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={follower.sizingValue}
                        onChange={(e) => {
                          updateFollower(index, { sizingValue: e.target.value });
                        }}
                        placeholder="Size"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>

            {!isEditing ? (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={startAfterCreate}
                  onChange={(e) => {
                    setStartAfterCreate(e.target.checked);
                  }}
                  className="rounded border-zinc-600"
                />
                Start copying immediately
              </label>
            ) : null}

            {error ? <p className="text-sm text-red-400">{error}</p> : null}

            <Button type="submit" className="w-full" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isEditing ? 'Saving…' : 'Creating…'}
                </>
              ) : isEditing ? (
                'Save changes'
              ) : (
                'Create copy group'
              )}
            </Button>
          </form>
        )}
      </SheetContent>
    </Sheet>
  );
}
