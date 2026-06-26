'use client';

import { LineChart } from 'lucide-react';

import type { AnalyticsOverview } from '@tradeflow/types/api';

import { Button, Skeleton } from '@tradeflow/ui';

import { AnalyticsMetricsGrid } from '@/features/analytics/components/analytics-stats-bar';
import {
  AverageRChart,
  CalendarHeatmap,
  DailyReturnsChart,
  DrawdownChart,
  EquityCurveChart,
  ExpectancyChart,
  HourDayHeatmap,
  MonthlyReturnsChart,
  PerformanceComparisonChart,
  ProfitFactorChart,
  RatioComparisonChart,
  StrategyPieChart,
  SymbolPieChart,
  WinLossPieChart,
  WinRateChart,
} from '@/features/analytics/components/analytics-charts';
import {
  AccountLeaderboard,
  StrategyLeaderboard,
} from '@/features/analytics/components/analytics-leaderboard';
import { useAnalyticsData } from '@/features/analytics/hooks/use-analytics-data';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6 p-4 sm:p-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-[360px]" />
        <Skeleton className="h-[360px]" />
      </div>
    </div>
  );
}

function deriveAvgWinLoss(data: AnalyticsOverview) {
  const winsSlice = data.win_loss_pie.find((s) => s.name === 'Wins');
  const lossSlice = data.win_loss_pie.find((s) => s.name === 'Losses');
  const avgWin =
    winsSlice && data.metrics.win_count > 0 ? winsSlice.value / data.metrics.win_count : 0;
  const avgLoss =
    lossSlice && data.metrics.loss_count > 0 ? lossSlice.value / data.metrics.loss_count : 0;
  return { avgWin, avgLoss };
}

export function AnalyticsPage() {
  const { data, loading, error, refetch } = useAnalyticsData();

  if (loading) {
    return <AnalyticsSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="p-4 sm:p-6">
        <EmptyState
          icon={LineChart}
          title="Could not load analytics"
          description={error ?? 'No analytics data available yet.'}
          action={
            <Button size="sm" onClick={() => void refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  const { avgWin, avgLoss } = deriveAvgWinLoss(data);

  return (
    <FadeInStagger className="space-y-6 p-4 sm:p-6">
      <FadeInItem>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <LineChart className="text-primary h-5 w-5" />
              <h1 className="text-xl font-semibold tracking-tight">Enterprise Analytics</h1>
            </div>
            <p className="text-muted-foreground mt-1 text-sm">
              Institutional-grade performance metrics, risk ratios, and comparative analysis
            </p>
          </div>
          <p className="text-muted-foreground text-xs tabular-nums">
            {data.metrics.total_trades.toLocaleString()} trades ·{' '}
            {data.metrics.starting_equity.toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
              maximumFractionDigits: 0,
            })}{' '}
            →{' '}
            {data.metrics.ending_equity.toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
              maximumFractionDigits: 0,
            })}
          </p>
        </div>
      </FadeInItem>

      <FadeInItem>
        <AnalyticsMetricsGrid metrics={data.metrics} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <EquityCurveChart data={data.equity_curve} />
        <DrawdownChart data={data.drawdown} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <WinRateChart
          winRate={data.metrics.win_rate}
          winCount={data.metrics.win_count}
          lossCount={data.metrics.loss_count}
        />
        <ProfitFactorChart
          profitFactor={data.metrics.profit_factor}
          winRate={data.metrics.win_rate}
        />
        <ExpectancyChart
          expectancy={data.metrics.expectancy}
          winRate={data.metrics.win_rate}
          avgWin={avgWin}
          avgLoss={avgLoss}
        />
        <AverageRChart averageR={data.metrics.average_r} winRate={data.metrics.win_rate} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2">
        <DailyReturnsChart data={data.daily_returns} />
        <MonthlyReturnsChart data={data.monthly_returns} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 lg:grid-cols-2">
        <CalendarHeatmap data={data.calendar_heatmap} />
        <HourDayHeatmap data={data.hour_heatmap} />
      </FadeInItem>

      <FadeInItem>
        <RatioComparisonChart
          sharpe={data.metrics.sharpe_ratio}
          sortino={data.metrics.sortino_ratio}
          averageR={data.metrics.average_r}
          profitFactor={data.metrics.profit_factor}
        />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-3">
        <WinLossPieChart data={data.win_loss_pie} />
        <SymbolPieChart data={data.symbol_pie} />
        <StrategyPieChart data={data.strategy_pie} />
      </FadeInItem>

      <FadeInItem>
        <PerformanceComparisonChart series={data.comparison} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <AccountLeaderboard entries={data.account_leaderboard} />
        <StrategyLeaderboard entries={data.strategy_leaderboard} />
      </FadeInItem>
    </FadeInStagger>
  );
}
