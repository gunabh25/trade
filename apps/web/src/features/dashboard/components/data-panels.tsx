'use client';

import { Briefcase, Link2, ListOrdered } from 'lucide-react';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  cn,
} from '@tradeflow/ui';

import { EmptyState, PnlText } from '@/features/dashboard/components/motion-primitives';

import type {
  ConnectedAccount,
  Order,
  Position,
} from '@/features/dashboard/data/mock-dashboard-data';
import { formatCurrency } from '@/features/dashboard/data/mock-dashboard-data';

const statusColors = {
  connected: 'profit',
  disconnected: 'secondary',
  error: 'loss',
} as const;

export function OpenPositionsTable({ positions }: { positions: Position[] }) {
  if (positions.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No open positions"
        description="When you have active trades, they'll appear here in real time."
        action={
          <Button variant="outline" size="sm">
            Connect an account
          </Button>
        }
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-border text-muted-foreground border-b text-left text-xs">
            <th className="pb-3 pr-4 font-medium">Symbol</th>
            <th className="pb-3 pr-4 font-medium">Side</th>
            <th className="pb-3 pr-4 font-medium">Qty</th>
            <th className="pb-3 pr-4 font-medium">Entry</th>
            <th className="pb-3 pr-4 font-medium">Mark</th>
            <th className="pb-3 text-right font-medium">PnL</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <tr key={position.id} className="border-border/50 border-b last:border-0">
              <td className="py-3 pr-4 font-medium tabular-nums">{position.symbol}</td>
              <td className="py-3 pr-4">
                <Badge
                  variant={position.side === 'long' ? 'profit' : 'loss'}
                  className="capitalize"
                >
                  {position.side}
                </Badge>
              </td>
              <td className="text-muted-foreground py-3 pr-4 tabular-nums">{position.quantity}</td>
              <td className="text-muted-foreground py-3 pr-4 tabular-nums">
                {formatCurrency(position.entryPrice)}
              </td>
              <td className="py-3 pr-4 tabular-nums">{formatCurrency(position.markPrice)}</td>
              <td className="py-3 text-right">
                <PnlText value={position.pnl} className="font-medium tabular-nums" />
                <span
                  className={cn(
                    'ml-1 text-xs',
                    position.pnlPercent >= 0 ? 'text-profit' : 'text-loss',
                  )}
                >
                  ({position.pnlPercent >= 0 ? '+' : ''}
                  {position.pnlPercent.toFixed(2)}%)
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function OpenOrdersTable({ orders }: { orders: Order[] }) {
  if (orders.length === 0) {
    return (
      <EmptyState
        icon={ListOrdered}
        title="No open orders"
        description="Pending limit, stop, and market orders will show here."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-border text-muted-foreground border-b text-left text-xs">
            <th className="pb-3 pr-4 font-medium">Symbol</th>
            <th className="pb-3 pr-4 font-medium">Side</th>
            <th className="pb-3 pr-4 font-medium">Type</th>
            <th className="pb-3 pr-4 font-medium">Qty</th>
            <th className="pb-3 pr-4 font-medium">Price</th>
            <th className="pb-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id} className="border-border/50 border-b last:border-0">
              <td className="py-3 pr-4 font-medium tabular-nums">{order.symbol}</td>
              <td className="text-muted-foreground py-3 pr-4 capitalize">{order.side}</td>
              <td className="text-muted-foreground py-3 pr-4">{order.type}</td>
              <td className="py-3 pr-4 tabular-nums">{order.quantity}</td>
              <td className="py-3 pr-4 tabular-nums">{formatCurrency(order.price)}</td>
              <td className="py-3">
                <Badge variant="outline" className="capitalize">
                  {order.status}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ConnectedAccountsList({ accounts }: { accounts: ConnectedAccount[] }) {
  if (accounts.length === 0) {
    return (
      <EmptyState
        icon={Link2}
        title="No connected accounts"
        description="Link your broker accounts to start copy trading and analytics."
        action={<Button size="sm">Add account</Button>}
      />
    );
  }

  return (
    <div className="space-y-3">
      {accounts.map((account) => (
        <div
          key={account.id}
          className="border-border/60 bg-muted/20 flex items-center justify-between rounded-md border px-4 py-3"
        >
          <div>
            <p className="text-sm font-medium">{account.name}</p>
            <p className="text-muted-foreground text-xs">{account.broker}</p>
          </div>
          <div className="text-right">
            <Badge variant={statusColors[account.status]}>{account.status}</Badge>
            <p className="text-muted-foreground mt-1 text-xs tabular-nums">
              {account.equity > 0 ? formatCurrency(account.equity) : '—'} · {account.lastSync}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function RiskStatusPanel({
  riskStatus,
  riskScore,
}: {
  riskStatus: 'low' | 'medium' | 'high';
  riskScore: number;
}) {
  const riskColors = {
    low: 'text-profit',
    medium: 'text-yellow-500',
    high: 'text-loss',
  };

  const riskLabels = {
    low: 'Within limits',
    medium: 'Approaching limits',
    high: 'Action required',
  };

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Risk Status</CardTitle>
        <CardDescription>Real-time risk monitoring</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <p
              className={cn(
                'text-3xl font-semibold capitalize tabular-nums',
                riskColors[riskStatus],
              )}
            >
              {riskStatus}
            </p>
            <p className="text-muted-foreground text-sm">{riskLabels[riskStatus]}</p>
          </div>
          <p className="text-2xl font-semibold tabular-nums">{riskScore}</p>
        </div>
        <div className="bg-muted h-2 overflow-hidden rounded-full">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              riskStatus === 'low' && 'bg-profit',
              riskStatus === 'medium' && 'bg-yellow-500',
              riskStatus === 'high' && 'bg-loss',
            )}
            style={{ width: `${riskScore}%` }}
          />
        </div>
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="bg-muted/40 rounded-md p-2">
            <p className="text-muted-foreground">Daily DD</p>
            <p className="font-medium tabular-nums">1.2%</p>
          </div>
          <div className="bg-muted/40 rounded-md p-2">
            <p className="text-muted-foreground">Max DD</p>
            <p className="font-medium tabular-nums">4.8%</p>
          </div>
          <div className="bg-muted/40 rounded-md p-2">
            <p className="text-muted-foreground">Exposure</p>
            <p className="font-medium tabular-nums">38%</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
