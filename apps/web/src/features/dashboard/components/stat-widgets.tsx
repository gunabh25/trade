'use client';

import {
  Activity,
  ArrowUpRight,
  Briefcase,
  CircleDollarSign,
  Link2,
  Shield,
  TrendingUp,
  Wallet,
  type LucideIcon,
} from 'lucide-react';

import { Card, CardContent, cn, Skeleton } from '@tradeflow/ui';

import { PnlText } from '@/features/dashboard/components/motion-primitives';

interface StatWidgetProps {
  label: string;
  value: React.ReactNode;
  subValue?: React.ReactNode;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
}

export function StatWidget({ label, value, subValue, icon: Icon, trend }: StatWidgetProps) {
  return (
    <Card className="border-border/60 bg-card/80 hover:border-border shadow-none transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-muted-foreground text-xs font-medium uppercase tracking-wider">
              {label}
            </p>
            <div className="text-2xl font-semibold tabular-nums tracking-tight">{value}</div>
            {subValue ? <div className="text-muted-foreground text-xs">{subValue}</div> : null}
          </div>
          <div
            className={cn(
              'flex h-9 w-9 items-center justify-center rounded-md',
              trend === 'up' && 'bg-profit/10 text-profit',
              trend === 'down' && 'bg-loss/10 text-loss',
              (!trend || trend === 'neutral') && 'bg-muted text-muted-foreground',
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function StatWidgetSkeleton() {
  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardContent className="p-5">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="mt-3 h-8 w-32" />
        <Skeleton className="mt-2 h-3 w-20" />
      </CardContent>
    </Card>
  );
}

export function StatWidgetsGrid({
  stats,
}: {
  stats: {
    totalEquity: number;
    todayPnl: number;
    todayPnlPercent: number;
    monthlyPnl: number;
    monthlyPnlPercent: number;
    openPositions: number;
    openOrders: number;
    connectedAccounts: number;
    riskStatus: string;
    riskScore: number;
  };
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatWidget
        label="Total Equity"
        value={stats.totalEquity.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
        subValue="Across all connected accounts"
        icon={Wallet}
        trend="neutral"
      />
      <StatWidget
        label="Today's PnL"
        value={<PnlText value={stats.todayPnl} />}
        subValue={
          <span className={stats.todayPnlPercent >= 0 ? 'text-profit' : 'text-loss'}>
            {stats.todayPnlPercent >= 0 ? '+' : ''}
            {stats.todayPnlPercent.toFixed(2)}% today
          </span>
        }
        icon={TrendingUp}
        trend={stats.todayPnl >= 0 ? 'up' : 'down'}
      />
      <StatWidget
        label="Monthly PnL"
        value={<PnlText value={stats.monthlyPnl} />}
        subValue={
          <span className={stats.monthlyPnlPercent >= 0 ? 'text-profit' : 'text-loss'}>
            {stats.monthlyPnlPercent >= 0 ? '+' : ''}
            {stats.monthlyPnlPercent.toFixed(2)}% MTD
          </span>
        }
        icon={ArrowUpRight}
        trend={stats.monthlyPnl >= 0 ? 'up' : 'down'}
      />
      <StatWidget
        label="Open Positions"
        value={stats.openPositions}
        subValue={`${stats.openOrders} pending orders`}
        icon={Briefcase}
      />
      <StatWidget
        label="Open Orders"
        value={stats.openOrders}
        subValue="Active limit & stop orders"
        icon={Activity}
      />
      <StatWidget
        label="Connected Accounts"
        value={stats.connectedAccounts}
        subValue="Live broker connections"
        icon={Link2}
      />
      <StatWidget
        label="Risk Status"
        value={<span className="capitalize">{stats.riskStatus}</span>}
        subValue={`Risk score: ${stats.riskScore}/100`}
        icon={Shield}
        trend={stats.riskStatus === 'low' ? 'up' : stats.riskStatus === 'high' ? 'down' : 'neutral'}
      />
      <StatWidget
        label="Available Margin"
        value={(stats.totalEquity * 0.42).toLocaleString('en-US', {
          style: 'currency',
          currency: 'USD',
        })}
        subValue="42% of equity available"
        icon={CircleDollarSign}
      />
    </div>
  );
}
