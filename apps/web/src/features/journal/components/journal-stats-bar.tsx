'use client';

import { BarChart3, Percent, Target, TrendingDown, TrendingUp, Trophy } from 'lucide-react';

import { Card, CardContent, cn } from '@tradeflow/ui';

import { formatCurrency } from '@/features/journal/utils/format';
import type { JournalStats } from '@tradeflow/types/api';

interface JournalStatsBarProps {
  stats: JournalStats;
}

export function JournalStatsBar({ stats }: JournalStatsBarProps) {
  const widgets = [
    {
      label: 'Total P&L',
      value: formatCurrency(stats.total_pnl),
      icon: stats.total_pnl >= 0 ? TrendingUp : TrendingDown,
      positive: stats.total_pnl >= 0,
    },
    {
      label: 'Win Rate',
      value: `${stats.win_rate.toFixed(1)}%`,
      icon: Percent,
      sub: `${String(stats.win_count)}W / ${String(stats.loss_count)}L`,
    },
    {
      label: 'Profit Factor',
      value: stats.profit_factor?.toFixed(2) ?? '—',
      icon: BarChart3,
    },
    {
      label: 'Avg Win',
      value: formatCurrency(stats.avg_win),
      icon: Trophy,
      positive: true,
    },
    {
      label: 'Avg Loss',
      value: formatCurrency(-Math.abs(stats.avg_loss)),
      icon: TrendingDown,
      positive: false,
    },
    {
      label: 'Best / Worst',
      value: `${formatCurrency(stats.best_trade ?? 0)} / ${formatCurrency(stats.worst_trade ?? 0)}`,
      icon: Target,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {widgets.map((widget) => {
        const Icon = widget.icon;
        return (
          <Card key={widget.label} className="border-border/60 bg-card/80 shadow-none">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-muted-foreground text-[11px] font-medium uppercase tracking-wider">
                  {widget.label}
                </p>
                <Icon className="text-muted-foreground h-3.5 w-3.5" />
              </div>
              <p
                className={cn(
                  'mt-1.5 text-lg font-semibold tracking-tight',
                  widget.positive === true && 'text-profit',
                  widget.positive === false && 'text-loss',
                )}
              >
                {widget.value}
              </p>
              {widget.sub ? (
                <p className="text-muted-foreground mt-0.5 text-[10px]">{widget.sub}</p>
              ) : null}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
