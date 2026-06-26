'use client';

import type { AnalyticsOverview } from '@tradeflow/types/api';

import { FadeInItem, FadeInStagger } from '@/features/dashboard/components/motion-primitives';
import {
  AccountLeaderboard,
  StrategyLeaderboard,
} from '@/features/analytics/components/analytics-leaderboard';
import {
  AvgWinLossChart,
  AverageRChart,
  CalendarHeatmap,
  DailyReturnsChart,
  DrawdownChart,
  EquityCurveChart,
  ExpectancyChart,
  HourDayHeatmap,
  LossRateChart,
  MonthlyReturnsChart,
  PerformanceComparisonChart,
  ProfitCurveChart,
  ProfitFactorChart,
  RatioComparisonChart,
  RecoveryFactorChart,
  SessionPerformanceChart,
  StreakMetricsChart,
  StrategyComparisonChart,
  StrategyPieChart,
  SymbolPerformanceChart,
  SymbolPieChart,
  TradeDistributionChart,
  WinLossPieChart,
  WinRateChart,
} from '@/features/analytics/components/analytics-charts';

interface AnalyticsChartSectionsProps {
  data: AnalyticsOverview;
}

export function AnalyticsChartSections({ data }: AnalyticsChartSectionsProps) {
  return (
    <FadeInStagger className="space-y-6">
      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <EquityCurveChart data={data.equity_curve} />
        <ProfitCurveChart data={data.profit_curve} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <DrawdownChart data={data.drawdown} />
        <TradeDistributionChart data={data.trade_distribution} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <WinRateChart
          winRate={data.metrics.win_rate}
          winCount={data.metrics.win_count}
          lossCount={data.metrics.loss_count}
        />
        <LossRateChart
          lossRate={data.metrics.loss_rate}
          lossCount={data.metrics.loss_count}
          winCount={data.metrics.win_count}
        />
        <ProfitFactorChart
          profitFactor={data.metrics.profit_factor}
          winRate={data.metrics.win_rate}
        />
        <ExpectancyChart
          expectancy={data.metrics.expectancy}
          winRate={data.metrics.win_rate}
          avgWin={data.metrics.avg_win}
          avgLoss={data.metrics.avg_loss}
        />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <AvgWinLossChart avgWin={data.metrics.avg_win} avgLoss={data.metrics.avg_loss} />
        <AverageRChart averageR={data.metrics.average_r} winRate={data.metrics.win_rate} />
        <RecoveryFactorChart
          recoveryFactor={data.metrics.recovery_factor}
          maxDrawdownDollars={data.metrics.max_drawdown_dollars}
        />
        <StreakMetricsChart
          maxWins={data.metrics.max_consecutive_wins}
          maxLosses={data.metrics.max_consecutive_losses}
        />
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

      <FadeInItem className="grid gap-4 lg:grid-cols-2">
        <SymbolPerformanceChart data={data.symbol_performance} />
        <SessionPerformanceChart data={data.session_performance} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-3">
        <WinLossPieChart data={data.win_loss_pie} />
        <SymbolPieChart data={data.symbol_pie} />
        <StrategyPieChart data={data.strategy_pie} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <PerformanceComparisonChart series={data.comparison} />
        <StrategyComparisonChart series={data.strategy_comparison} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 xl:grid-cols-2">
        <AccountLeaderboard entries={data.account_leaderboard} />
        <StrategyLeaderboard entries={data.strategy_leaderboard} />
      </FadeInItem>
    </FadeInStagger>
  );
}
