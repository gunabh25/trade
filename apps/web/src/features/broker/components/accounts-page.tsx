'use client';

import { Link2, Loader2, Plus, RefreshCw, ShoppingCart, Trash2, Unplug } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import type { BrokerConnection, TradingAccount } from '@tradeflow/types/api';

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

import * as brokerApi from '@/features/broker/api/broker-api';
import { ConnectBrokerSheet } from '@/features/broker/components/connect-broker-sheet';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';
import { ApiClientError } from '@/lib/errors';

interface AccountsPageContentProps {
  autoOpenConnect?: boolean;
}

export function AccountsPageContent({ autoOpenConnect = false }: AccountsPageContentProps) {
  const [connections, setConnections] = useState<BrokerConnection[]>([]);
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectOpen, setConnectOpen] = useState(autoOpenConnect);
  const [orderAccount, setOrderAccount] = useState<TradingAccount | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextConnections, nextAccounts] = await Promise.all([
        brokerApi.listBrokerConnections(),
        brokerApi.listTradingAccounts(),
      ]);
      setConnections(nextConnections);
      setAccounts(nextAccounts);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runConnectionAction(
    connectionId: string,
    action: 'connect' | 'disconnect' | 'sync' | 'delete',
  ) {
    setActionId(connectionId);
    setError(null);
    try {
      if (action === 'connect') {
        await brokerApi.connectBroker(connectionId);
      } else if (action === 'disconnect') {
        await brokerApi.disconnectBroker(connectionId);
      } else if (action === 'delete') {
        await brokerApi.deleteBrokerConnection(connectionId);
      } else {
        await brokerApi.syncTradingAccounts(connectionId);
      }
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
          <h1 className="text-2xl font-semibold tracking-tight">Trading Accounts</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Connect brokers and link trading accounts for copy groups and analytics.
          </p>
        </div>
        <Button
          onClick={() => {
            setConnectOpen(true);
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          Connect broker
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
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Broker connections</CardTitle>
            <CardDescription>Credentials are encrypted and stored securely.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {connections.length === 0 ? (
              <EmptyState
                icon={Link2}
                title="No broker connections"
                description="Connect Paper Trading to try the platform instantly, or link Tradovate/Binance."
                action={
                  <Button
                    size="sm"
                    onClick={() => {
                      setConnectOpen(true);
                    }}
                  >
                    Connect broker
                  </Button>
                }
              />
            ) : (
              connections.map((connection) => (
                <div
                  key={connection.id}
                  className="border-border flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"
                >
                  <div>
                    <p className="font-medium">{connection.name}</p>
                    <p className="text-muted-foreground text-sm">
                      {connection.broker} · {connection.status}
                    </p>
                    {connection.last_error ? (
                      <p className="mt-1 text-xs text-red-400">{connection.last_error}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {connection.status !== 'connected' ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={actionId === connection.id}
                        onClick={() => void runConnectionAction(connection.id, 'connect')}
                      >
                        Connect
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={actionId === connection.id}
                        onClick={() => void runConnectionAction(connection.id, 'sync')}
                      >
                        <RefreshCw className="mr-1 h-3.5 w-3.5" />
                        Sync
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={actionId === connection.id}
                      onClick={() => void runConnectionAction(connection.id, 'disconnect')}
                    >
                      <Unplug className="mr-1 h-3.5 w-3.5" />
                      Disconnect
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-400 hover:text-red-300"
                      disabled={actionId === connection.id}
                      onClick={() => void runConnectionAction(connection.id, 'delete')}
                    >
                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                      Remove
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </FadeInItem>

      <FadeInItem>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Linked trading accounts</CardTitle>
            <CardDescription>
              These accounts can be used as leaders or followers in copy groups.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {accounts.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Connect a broker to import trading accounts automatically.
              </p>
            ) : (
              accounts.map((account) => (
                <div
                  key={account.id}
                  className="border-border flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"
                >
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-muted-foreground text-sm">
                      {account.broker} · {account.account_type} · {account.account_role}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {account.account_role === 'leader' ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setOrderAccount(account);
                        }}
                      >
                        <ShoppingCart className="mr-1 h-3.5 w-3.5" />
                        Place test order
                      </Button>
                    ) : null}
                    <Badge variant="outline">{account.status}</Badge>
                    {account.balance != null ? (
                      <span className="text-sm font-medium">
                        {account.balance.toLocaleString(undefined, {
                          style: 'currency',
                          currency: account.currency || 'USD',
                        })}
                      </span>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </FadeInItem>

      <ConnectBrokerSheet
        open={connectOpen}
        onOpenChange={setConnectOpen}
        onConnected={() => void load()}
      />
      <PlaceTestOrderSheet
        account={orderAccount}
        open={orderAccount !== null}
        onOpenChange={(open) => {
          if (!open) setOrderAccount(null);
        }}
      />
    </FadeInStagger>
  );
}

interface PlaceTestOrderSheetProps {
  account: TradingAccount | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function PlaceTestOrderSheet({ account, open, onOpenChange }: PlaceTestOrderSheetProps) {
  const [symbol, setSymbol] = useState('AAPL');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('1');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setSymbol('AAPL');
    setSide('buy');
    setQuantity('1');
    setError(null);
    setSuccess(null);
  }, [open, account?.id]);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!account) return;

    const parsedQuantity = Number(quantity);
    if (!symbol.trim()) {
      setError('Enter a symbol.');
      return;
    }
    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError('Quantity must be greater than zero.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const order = await brokerApi.placeBrokerOrder(account.broker_connection_id, {
        account_id: account.external_account_id,
        symbol: symbol.trim().toUpperCase(),
        side,
        order_type: 'market',
        quantity: parsedQuantity,
      });
      setSuccess(`Placed ${order.side} ${order.quantity} ${order.symbol}.`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to place test order');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="text-left">
          <SheetTitle>Place test order</SheetTitle>
        </SheetHeader>

        {account ? (
          <form onSubmit={(event) => void handleSubmit(event)} className="mt-6 space-y-5">
            <div className="space-y-1">
              <p className="text-sm font-medium">{account.name}</p>
              <p className="text-muted-foreground text-xs">
                {account.broker} · {account.account_role} · {account.account_type}
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="test-order-symbol" className="text-sm font-medium">
                Symbol
              </label>
              <Input
                id="test-order-symbol"
                value={symbol}
                onChange={(e) => {
                  setSymbol(e.target.value);
                }}
                placeholder="AAPL"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Side</label>
              <div className="grid grid-cols-2 gap-2">
                {(['buy', 'sell'] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => {
                      setSide(value);
                    }}
                    className={`rounded-lg border px-3 py-2 text-sm capitalize ${
                      side === value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-accent/40'
                    }`}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="test-order-quantity" className="text-sm font-medium">
                Quantity
              </label>
              <Input
                id="test-order-quantity"
                type="number"
                min="0.01"
                step="0.01"
                value={quantity}
                onChange={(e) => {
                  setQuantity(e.target.value);
                }}
                required
              />
            </div>

            <p className="text-muted-foreground text-xs">
              This submits a market order to the paper leader account so you can verify copy
              trading.
            </p>

            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            {success ? <p className="text-sm text-emerald-400">{success}</p> : null}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Placing order…
                </>
              ) : (
                'Place test order'
              )}
            </Button>
          </form>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
