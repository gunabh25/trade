import type {
  AnalyticsDistributionBucket,
  AnalyticsOverview,
  AnalyticsOverviewQuery,
  AnalyticsProfitCurvePoint,
  AnalyticsSessionPerformance,
  AnalyticsSymbolPerformance,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toNumber, toString } from '@/lib/api/normalize';

function getApiBaseUrl(): string {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : undefined);
  if (!baseUrl) {
    throw new Error('NEXT_PUBLIC_API_URL is not configured');
  }
  return baseUrl.replace(/\/$/, '');
}

function getApiVersion(): string {
  return process.env.NEXT_PUBLIC_API_VERSION ?? 'v1';
}

function buildQueryString(query: AnalyticsOverviewQuery): string {
  const params = new URLSearchParams();
  if (query.date_from) params.set('date_from', query.date_from);
  if (query.date_to) params.set('date_to', query.date_to);
  if (query.trading_account_id) params.set('trading_account_id', query.trading_account_id);
  if (query.strategy_id) params.set('strategy_id', query.strategy_id);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

function normalizeOverview(raw: Record<string, unknown>): AnalyticsOverview {
  const metricsRaw = (
    typeof raw.metrics === 'object' && raw.metrics !== null ? raw.metrics : {}
  ) as Record<string, unknown>;

  const mapEquity = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      date: toString(point.date),
      equity: toNumber(point.equity),
    }));

  const mapProfitCurve = (items: unknown[]): AnalyticsProfitCurvePoint[] =>
    (items as Record<string, unknown>[]).map((point) => ({
      trade_index: toNumber(point.trade_index),
      cumulative_pnl: toNumber(point.cumulative_pnl),
    }));

  const mapDrawdown = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      date: toString(point.date),
      drawdown_pct: toNumber(point.drawdown_pct),
    }));

  const mapReturns = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      label: toString(point.label),
      value: toNumber(point.value),
    }));

  const mapCalendar = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      date: toString(point.date),
      pnl: toNumber(point.pnl),
      trade_count: toNumber(point.trade_count),
    }));

  const mapHour = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      day_of_week: toNumber(point.day_of_week),
      hour: toNumber(point.hour),
      pnl: toNumber(point.pnl),
      trade_count: toNumber(point.trade_count),
    }));

  const mapDistribution = (items: unknown[]): AnalyticsDistributionBucket[] =>
    (items as Record<string, unknown>[]).map((point) => ({
      label: toString(point.label),
      count: toNumber(point.count),
    }));

  const mapPie = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      name: toString(point.name),
      value: toNumber(point.value),
      color: toNullableString(point.color),
    }));

  const mapSymbolPerformance = (items: unknown[]): AnalyticsSymbolPerformance[] =>
    (items as Record<string, unknown>[]).map((point) => ({
      symbol: toString(point.symbol),
      trade_count: toNumber(point.trade_count),
      total_pnl: toNumber(point.total_pnl),
      win_rate: toNumber(point.win_rate),
      avg_pnl: toNumber(point.avg_pnl),
    }));

  const mapSessionPerformance = (items: unknown[]): AnalyticsSessionPerformance[] =>
    (items as Record<string, unknown>[]).map((point) => ({
      session: toString(point.session),
      trade_count: toNumber(point.trade_count),
      total_pnl: toNumber(point.total_pnl),
      win_rate: toNumber(point.win_rate),
    }));

  const mapLeaderboard = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      rank: toNumber(point.rank),
      id: toString(point.id),
      name: toString(point.name),
      subtitle: toNullableString(point.subtitle),
      pnl: toNumber(point.pnl),
      win_rate: toNumber(point.win_rate),
      profit_factor: point.profit_factor != null ? toNumber(point.profit_factor) : null,
      trade_count: toNumber(point.trade_count),
      sharpe_ratio: point.sharpe_ratio != null ? toNumber(point.sharpe_ratio) : null,
    }));

  const mapComparison = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((series) => ({
      id: toString(series.id),
      name: toString(series.name),
      color: toString(series.color),
      points: mapEquity(Array.isArray(series.points) ? series.points : []),
    }));

  return {
    metrics: {
      total_trades: toNumber(metricsRaw.total_trades),
      total_pnl: toNumber(metricsRaw.total_pnl),
      win_count: toNumber(metricsRaw.win_count),
      loss_count: toNumber(metricsRaw.loss_count),
      breakeven_count: toNumber(metricsRaw.breakeven_count),
      win_rate: toNumber(metricsRaw.win_rate),
      loss_rate: toNumber(metricsRaw.loss_rate),
      avg_win: toNumber(metricsRaw.avg_win),
      avg_loss: toNumber(metricsRaw.avg_loss),
      profit_factor: metricsRaw.profit_factor != null ? toNumber(metricsRaw.profit_factor) : null,
      expectancy: toNumber(metricsRaw.expectancy),
      average_r: metricsRaw.average_r != null ? toNumber(metricsRaw.average_r) : null,
      sharpe_ratio: metricsRaw.sharpe_ratio != null ? toNumber(metricsRaw.sharpe_ratio) : null,
      sortino_ratio: metricsRaw.sortino_ratio != null ? toNumber(metricsRaw.sortino_ratio) : null,
      max_drawdown_pct: toNumber(metricsRaw.max_drawdown_pct),
      max_drawdown_dollars: toNumber(metricsRaw.max_drawdown_dollars),
      recovery_factor:
        metricsRaw.recovery_factor != null ? toNumber(metricsRaw.recovery_factor) : null,
      max_consecutive_wins: toNumber(metricsRaw.max_consecutive_wins),
      max_consecutive_losses: toNumber(metricsRaw.max_consecutive_losses),
      starting_equity: toNumber(metricsRaw.starting_equity),
      ending_equity: toNumber(metricsRaw.ending_equity),
    },
    equity_curve: mapEquity(Array.isArray(raw.equity_curve) ? raw.equity_curve : []),
    profit_curve: mapProfitCurve(Array.isArray(raw.profit_curve) ? raw.profit_curve : []),
    drawdown: mapDrawdown(Array.isArray(raw.drawdown) ? raw.drawdown : []),
    daily_returns: mapReturns(Array.isArray(raw.daily_returns) ? raw.daily_returns : []),
    monthly_returns: mapReturns(Array.isArray(raw.monthly_returns) ? raw.monthly_returns : []),
    calendar_heatmap: mapCalendar(Array.isArray(raw.calendar_heatmap) ? raw.calendar_heatmap : []),
    hour_heatmap: mapHour(Array.isArray(raw.hour_heatmap) ? raw.hour_heatmap : []),
    trade_distribution: mapDistribution(
      Array.isArray(raw.trade_distribution) ? raw.trade_distribution : [],
    ),
    win_loss_pie: mapPie(Array.isArray(raw.win_loss_pie) ? raw.win_loss_pie : []),
    symbol_pie: mapPie(Array.isArray(raw.symbol_pie) ? raw.symbol_pie : []),
    strategy_pie: mapPie(Array.isArray(raw.strategy_pie) ? raw.strategy_pie : []),
    symbol_performance: mapSymbolPerformance(
      Array.isArray(raw.symbol_performance) ? raw.symbol_performance : [],
    ),
    session_performance: mapSessionPerformance(
      Array.isArray(raw.session_performance) ? raw.session_performance : [],
    ),
    account_leaderboard: mapLeaderboard(
      Array.isArray(raw.account_leaderboard) ? raw.account_leaderboard : [],
    ),
    strategy_leaderboard: mapLeaderboard(
      Array.isArray(raw.strategy_leaderboard) ? raw.strategy_leaderboard : [],
    ),
    comparison: mapComparison(Array.isArray(raw.comparison) ? raw.comparison : []),
    strategy_comparison: mapComparison(
      Array.isArray(raw.strategy_comparison) ? raw.strategy_comparison : [],
    ),
  };
}

export async function getAnalyticsOverview(
  query: AnalyticsOverviewQuery = {},
): Promise<AnalyticsOverview> {
  const response = await apiRequest<Record<string, unknown>>(
    `/analytics/overview${buildQueryString(query)}`,
  );
  return normalizeOverview(response.data);
}

export async function downloadAnalyticsExport(
  format: 'csv' | 'pdf',
  query: AnalyticsOverviewQuery = {},
): Promise<void> {
  const url = `${getApiBaseUrl()}/api/${getApiVersion()}/analytics/export/${format}${buildQueryString(query)}`;
  const response = await fetch(url, { credentials: 'include' });
  if (!response.ok) throw new Error(`Export failed (${String(response.status)})`);

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = `analytics-report.${format}`;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export type { AnalyticsOverviewQuery };
