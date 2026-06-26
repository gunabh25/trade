import type { AnalyticsOverview } from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toNumber, toString } from '@/lib/api/normalize';

export interface AnalyticsOverviewQuery {
  date_from?: string;
  date_to?: string;
  trading_account_id?: string;
  strategy_id?: string;
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

  const mapPie = (items: unknown[]) =>
    (items as Record<string, unknown>[]).map((point) => ({
      name: toString(point.name),
      value: toNumber(point.value),
      color: toNullableString(point.color),
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
      profit_factor: metricsRaw.profit_factor != null ? toNumber(metricsRaw.profit_factor) : null,
      expectancy: toNumber(metricsRaw.expectancy),
      average_r: metricsRaw.average_r != null ? toNumber(metricsRaw.average_r) : null,
      sharpe_ratio: metricsRaw.sharpe_ratio != null ? toNumber(metricsRaw.sharpe_ratio) : null,
      sortino_ratio: metricsRaw.sortino_ratio != null ? toNumber(metricsRaw.sortino_ratio) : null,
      max_drawdown_pct: toNumber(metricsRaw.max_drawdown_pct),
      starting_equity: toNumber(metricsRaw.starting_equity),
      ending_equity: toNumber(metricsRaw.ending_equity),
    },
    equity_curve: mapEquity(Array.isArray(raw.equity_curve) ? raw.equity_curve : []),
    drawdown: mapDrawdown(Array.isArray(raw.drawdown) ? raw.drawdown : []),
    daily_returns: mapReturns(Array.isArray(raw.daily_returns) ? raw.daily_returns : []),
    monthly_returns: mapReturns(Array.isArray(raw.monthly_returns) ? raw.monthly_returns : []),
    calendar_heatmap: mapCalendar(Array.isArray(raw.calendar_heatmap) ? raw.calendar_heatmap : []),
    hour_heatmap: mapHour(Array.isArray(raw.hour_heatmap) ? raw.hour_heatmap : []),
    win_loss_pie: mapPie(Array.isArray(raw.win_loss_pie) ? raw.win_loss_pie : []),
    symbol_pie: mapPie(Array.isArray(raw.symbol_pie) ? raw.symbol_pie : []),
    strategy_pie: mapPie(Array.isArray(raw.strategy_pie) ? raw.strategy_pie : []),
    account_leaderboard: mapLeaderboard(
      Array.isArray(raw.account_leaderboard) ? raw.account_leaderboard : [],
    ),
    strategy_leaderboard: mapLeaderboard(
      Array.isArray(raw.strategy_leaderboard) ? raw.strategy_leaderboard : [],
    ),
    comparison: mapComparison(Array.isArray(raw.comparison) ? raw.comparison : []),
  };
}

export async function getAnalyticsOverview(
  query: AnalyticsOverviewQuery = {},
): Promise<AnalyticsOverview> {
  const params = new URLSearchParams();
  if (query.date_from) params.set('date_from', query.date_from);
  if (query.date_to) params.set('date_to', query.date_to);
  if (query.trading_account_id) params.set('trading_account_id', query.trading_account_id);
  if (query.strategy_id) params.set('strategy_id', query.strategy_id);

  const qs = params.toString();
  const response = await apiRequest<Record<string, unknown>>(
    `/analytics/overview${qs ? `?${qs}` : ''}`,
  );
  return normalizeOverview(response.data);
}
