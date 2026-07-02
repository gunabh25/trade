'use client';

import { AlertTriangle, Plus, Shield } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import type { RiskBreach, RiskRule, RiskRuleConfig } from '@tradeflow/types/api';
import type { TradingAccount } from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@tradeflow/ui';

import { listTradingAccounts } from '@/features/broker/api/broker-api';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';
import * as riskApi from '@/features/risk/api/risk-api';
import { ApiClientError } from '@/lib/errors';

const emptyForm = (): RiskRuleConfig & { trading_account_id: string } => ({
  trading_account_id: '',
  name: 'Default',
  enabled: true,
  daily_loss_limit_usd: null,
  trailing_drawdown_limit_usd: null,
  max_position_size_usd: null,
  max_contracts_per_symbol: null,
  max_total_contracts: null,
  max_leverage: null,
  auto_flatten_on_breach: true,
  auto_stop_copying_on_breach: true,
});

function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function RiskRuleSheet({
  open,
  onOpenChange,
  accounts,
  initial,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accounts: TradingAccount[];
  initial: RiskRule | null;
  onSaved: () => void;
}) {
  const [form, setForm] = useState(emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setError(null);
    if (initial) {
      setForm({
        trading_account_id: initial.trading_account_id,
        name: initial.name,
        enabled: initial.enabled,
        daily_loss_limit_usd: initial.daily_loss_limit_usd,
        trailing_drawdown_limit_usd: initial.trailing_drawdown_limit_usd,
        max_position_size_usd: initial.max_position_size_usd,
        max_contracts_per_symbol: initial.max_contracts_per_symbol,
        max_total_contracts: initial.max_total_contracts,
        max_leverage: initial.max_leverage,
        auto_flatten_on_breach: initial.auto_flatten_on_breach,
        auto_stop_copying_on_breach: initial.auto_stop_copying_on_breach,
      });
    } else {
      setForm({
        ...emptyForm(),
        trading_account_id: accounts[0]?.id ?? '',
      });
    }
  }, [open, initial, accounts]);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.trading_account_id) {
      setError('Select a trading account.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload: RiskRuleConfig = {
        name: form.name ?? 'Default',
        enabled: form.enabled ?? true,
        daily_loss_limit_usd: form.daily_loss_limit_usd ?? null,
        trailing_drawdown_limit_usd: form.trailing_drawdown_limit_usd ?? null,
        max_position_size_usd: form.max_position_size_usd ?? null,
        max_contracts_per_symbol: form.max_contracts_per_symbol ?? null,
        max_total_contracts: form.max_total_contracts ?? null,
        max_leverage: form.max_leverage ?? null,
        auto_flatten_on_breach: form.auto_flatten_on_breach ?? true,
        auto_stop_copying_on_breach: form.auto_stop_copying_on_breach ?? true,
      };

      if (initial) {
        await riskApi.updateRiskRule(initial.id, payload);
      } else {
        await riskApi.createRiskRule({
          trading_account_id: form.trading_account_id,
          ...payload,
        });
      }
      onSaved();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to save risk rule');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="text-left">
          <SheetTitle>{initial ? 'Edit risk rule' : 'Create risk rule'}</SheetTitle>
        </SheetHeader>

        <form onSubmit={(event) => void handleSubmit(event)} className="mt-6 space-y-4">
          {!initial ? (
            <div className="space-y-2">
              <label className="text-sm font-medium">Trading account</label>
              <select
                value={form.trading_account_id}
                onChange={(e) => {
                  setForm((prev) => ({ ...prev, trading_account_id: e.target.value }));
                }}
                className="border-input bg-background h-10 w-full rounded-md border px-3 text-sm"
                required
              >
                <option value="">Select account…</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} · {account.broker} · {account.account_role}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div className="space-y-2">
            <label className="text-sm font-medium">Rule name</label>
            <Input
              value={form.name ?? ''}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, name: e.target.value }));
              }}
              required
            />
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.enabled ?? true}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, enabled: e.target.checked }));
              }}
            />
            Enabled
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            {(
              [
                ['daily_loss_limit_usd', 'Daily loss limit (USD)'],
                ['trailing_drawdown_limit_usd', 'Trailing drawdown (USD)'],
                ['max_position_size_usd', 'Max position size (USD)'],
                ['max_leverage', 'Max leverage'],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="space-y-2">
                <label className="text-sm font-medium">{label}</label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form[key] ?? ''}
                  onChange={(e) => {
                    setForm((prev) => ({ ...prev, [key]: parseOptionalNumber(e.target.value) }));
                  }}
                />
              </div>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Max contracts / symbol</label>
              <Input
                type="number"
                min="1"
                value={form.max_contracts_per_symbol ?? ''}
                onChange={(e) => {
                  const value = parseOptionalNumber(e.target.value);
                  setForm((prev) => ({
                    ...prev,
                    max_contracts_per_symbol: value != null ? Math.trunc(value) : null,
                  }));
                }}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Max total contracts</label>
              <Input
                type="number"
                min="1"
                value={form.max_total_contracts ?? ''}
                onChange={(e) => {
                  const value = parseOptionalNumber(e.target.value);
                  setForm((prev) => ({
                    ...prev,
                    max_total_contracts: value != null ? Math.trunc(value) : null,
                  }));
                }}
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.auto_flatten_on_breach ?? true}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, auto_flatten_on_breach: e.target.checked }));
              }}
            />
            Auto-flatten on breach
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.auto_stop_copying_on_breach ?? true}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, auto_stop_copying_on_breach: e.target.checked }));
              }}
            />
            Auto-stop copying on breach
          </label>

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Saving…' : initial ? 'Save changes' : 'Create rule'}
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
}

export function RiskPageContent() {
  const [rules, setRules] = useState<RiskRule[]>([]);
  const [breaches, setBreaches] = useState<RiskBreach[]>([]);
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<RiskRule | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextRules, nextBreaches, nextAccounts] = await Promise.all([
        riskApi.listRiskRules(),
        riskApi.listRiskBreaches(),
        listTradingAccounts(),
      ]);
      setRules(nextRules);
      setBreaches(nextBreaches);
      setAccounts(nextAccounts);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load risk data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function accountLabel(accountId: string): string {
    const account = accounts.find((item) => item.id === accountId);
    return account ? `${account.name} (${account.broker})` : accountId.slice(0, 8);
  }

  async function runRuleAction(
    ruleId: string,
    action: 'kill-on' | 'kill-off' | 'delete' | 'flatten',
    accountId?: string,
  ) {
    setActionId(ruleId);
    setError(null);
    try {
      if (action === 'kill-on') await riskApi.activateKillSwitch(ruleId);
      if (action === 'kill-off') await riskApi.deactivateKillSwitch(ruleId);
      if (action === 'delete') await riskApi.deleteRiskRule(ruleId);
      if (action === 'flatten' && accountId) await riskApi.flattenAccount(accountId);
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Action failed');
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
          <h1 className="text-2xl font-semibold tracking-tight">Risk Management</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Configure limits, kill switches, and review breach history.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditingRule(null);
            setSheetOpen(true);
          }}
          disabled={accounts.length === 0}
        >
          <Plus className="mr-2 h-4 w-4" />
          New rule
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
        {rules.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <EmptyState
                icon={Shield}
                title="No risk rules"
                description="Create a rule to monitor daily loss, position size, and activate kill switches."
                action={
                  <Button
                    size="sm"
                    disabled={accounts.length === 0}
                    onClick={() => {
                      setEditingRule(null);
                      setSheetOpen(true);
                    }}
                  >
                    Create rule
                  </Button>
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {rules.map((rule) => (
              <Card key={rule.id}>
                <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
                  <div>
                    <CardTitle className="text-base">{rule.name}</CardTitle>
                    <CardDescription>{accountLabel(rule.trading_account_id)}</CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={rule.enabled ? 'default' : 'outline'}>
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    {rule.kill_switch_active ? (
                      <Badge variant="destructive">Kill switch</Badge>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-muted-foreground text-sm">
                    Daily loss:{' '}
                    {rule.daily_loss_limit_usd != null ? `$${rule.daily_loss_limit_usd}` : '—'}
                    {' · '}
                    Max position:{' '}
                    {rule.max_position_size_usd != null ? `$${rule.max_position_size_usd}` : '—'}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingRule(rule);
                        setSheetOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    {rule.kill_switch_active ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={actionId === rule.id}
                        onClick={() => void runRuleAction(rule.id, 'kill-off')}
                      >
                        Deactivate kill switch
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={actionId === rule.id}
                        onClick={() => void runRuleAction(rule.id, 'kill-on')}
                      >
                        Activate kill switch
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionId === rule.id}
                      onClick={() =>
                        void runRuleAction(rule.id, 'flatten', rule.trading_account_id)
                      }
                    >
                      Flatten account
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={actionId === rule.id}
                      onClick={() => void runRuleAction(rule.id, 'delete')}
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </FadeInItem>

      <FadeInItem>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent breaches</CardTitle>
            <CardDescription>Risk limit violations and automated actions taken.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {breaches.length === 0 ? (
              <p className="text-muted-foreground text-sm">No breaches recorded.</p>
            ) : (
              breaches.slice(0, 10).map((breach) => (
                <div
                  key={breach.id}
                  className="border-border flex gap-3 rounded-lg border p-3 text-sm"
                >
                  <AlertTriangle className="text-destructive mt-0.5 h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-medium">{breach.message}</p>
                    <p className="text-muted-foreground text-xs">
                      {accountLabel(breach.trading_account_id)} · {breach.breach_type} ·{' '}
                      {new Date(breach.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </FadeInItem>

      <RiskRuleSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        accounts={accounts}
        initial={editingRule}
        onSaved={() => void load()}
      />
    </FadeInStagger>
  );
}
