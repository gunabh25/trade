'use client';

import {
  Activity,
  BarChart3,
  Flame,
  Percent,
  Scale,
  Sigma,
  Target,
  TrendingDown,
  TrendingUp,
  Trophy,
  Zap,
} from 'lucide-react';

import type { AnalyticsMetrics } from '@tradeflow/types/api';

import { Card, CardContent, cn } from '@tradeflow/ui';

import { formatCurrency, formatPercent, formatRatio } from '@/features/analytics/utils/format';

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'neutral';
}

function MetricCard({ label, value, sub, icon: Icon, trend = 'neutral' }: MetricCardProps) {
  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <p className="text-muted-foreground truncate text-[11px] font-medium uppercase tracking-wider">
              {label}
            </p>
            <p className="text-xl font-semibold tabular-nums tracking-tight sm:text-2xl">{value}</p>
            {sub ? <p className="text-muted-foreground text-xs">{sub}</p> : null}
          </div>
          <div
            className={cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-md',
              trend === 'up' && 'bg-profit/10 text-profit',
              trend === 'down' && 'bg-loss/10 text-loss',
              trend === 'neutral' && 'bg-muted text-muted-foreground',
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AnalyticsMetricsGrid({ metrics }: { metrics: AnalyticsMetrics }) {
  const pfTrend = (metrics.profit_factor ?? 0) >= 1.5 ? 'up' : 'neutral';
  const wrTrend = metrics.win_rate >= 55 ? 'up' : metrics.win_rate < 45 ? 'down' : 'neutral';

  const cards: MetricCardProps[] = [
    {
      label: 'Win Rate',
      value: `${metrics.win_rate.toFixed(1)}%`,
      sub: `${metrics.win_count}W · ${metrics.loss_count}L`,
      icon: Percent,
      trend: wrTrend,
    },
    {
      label: 'Loss Rate',
      value: `${metrics.loss_rate.toFixed(1)}%`,
      sub: `${metrics.loss_count} losses`,
      icon: TrendingDown,
      trend: metrics.loss_rate > 50 ? 'down' : 'neutral',
    },
    {
      label: 'Avg Win',
      value: formatCurrency(metrics.avg_win),
      sub: 'Per winning trade',
      icon: Trophy,
      trend: 'up',
    },
    {
      label: 'Avg Loss',
      value: formatCurrency(metrics.avg_loss),
      sub: 'Per losing trade',
      icon: TrendingDown,
      trend: 'down',
    },
    {
      label: 'Profit Factor',
      value: formatRatio(metrics.profit_factor),
      sub: 'Gross profit / gross loss',
      icon: BarChart3,
      trend: pfTrend,
    },
    {
      label: 'Expectancy',
      value: formatCurrency(metrics.expectancy),
      sub: 'Avg P&L per trade',
      icon: Target,
      trend: metrics.expectancy >= 0 ? 'up' : 'down',
    },
    {
      label: 'Sharpe Ratio',
      value: formatRatio(metrics.sharpe_ratio),
      sub: 'Risk-adjusted return',
      icon: Sigma,
      trend: (metrics.sharpe_ratio ?? 0) >= 1.5 ? 'up' : 'neutral',
    },
    {
      label: 'Sortino Ratio',
      value: formatRatio(metrics.sortino_ratio),
      sub: 'Downside-adjusted',
      icon: Activity,
      trend: (metrics.sortino_ratio ?? 0) >= 2 ? 'up' : 'neutral',
    },
    {
      label: 'Max Drawdown',
      value: formatPercent(metrics.max_drawdown_pct),
      sub: formatCurrency(Math.abs(metrics.max_drawdown_dollars)),
      icon: TrendingDown,
      trend: 'down',
    },
    {
      label: 'Recovery Factor',
      value: formatRatio(metrics.recovery_factor),
      sub: 'Profit / max DD',
      icon: Scale,
      trend: (metrics.recovery_factor ?? 0) >= 1 ? 'up' : 'neutral',
    },
    {
      label: 'Max Win Streak',
      value: String(metrics.max_consecutive_wins),
      sub: 'Consecutive wins',
      icon: Flame,
      trend: 'up',
    },
    {
      label: 'Max Loss Streak',
      value: String(metrics.max_consecutive_losses),
      sub: 'Consecutive losses',
      icon: Zap,
      trend: 'down',
    },
    {
      label: 'Average R',
      value: formatRatio(metrics.average_r),
      sub: 'R-multiple per trade',
      icon: Scale,
      trend: (metrics.average_r ?? 0) >= 1 ? 'up' : 'neutral',
    },
    {
      label: 'Total P&L',
      value: formatCurrency(metrics.total_pnl),
      sub: `${metrics.total_trades} trades`,
      icon: TrendingUp,
      trend: metrics.total_pnl >= 0 ? 'up' : 'down',
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
      {cards.map((card) => (
        <MetricCard key={card.label} {...card} />
      ))}
    </div>
  );
}
