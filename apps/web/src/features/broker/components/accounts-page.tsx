'use client';

import { Link2, Plus, RefreshCw, Unplug } from 'lucide-react';
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
    action: 'connect' | 'disconnect' | 'sync',
  ) {
    setActionId(connectionId);
    setError(null);
    try {
      if (action === 'connect') {
        await brokerApi.connectBroker(connectionId);
      } else if (action === 'disconnect') {
        await brokerApi.disconnectBroker(connectionId);
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
    </FadeInStagger>
  );
}
