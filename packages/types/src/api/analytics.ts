export interface AnalyticsMetrics {
  total_trades: number;
  total_pnl: number;
  win_count: number;
  loss_count: number;
  breakeven_count: number;
  win_rate: number;
  profit_factor: number | null;
  expectancy: number;
  average_r: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown_pct: number;
  starting_equity: number;
  ending_equity: number;
}

export interface AnalyticsEquityPoint {
  date: string;
  equity: number;
}

export interface AnalyticsDrawdownPoint {
  date: string;
  drawdown_pct: number;
}

export interface AnalyticsReturnPoint {
  label: string;
  value: number;
}

export interface AnalyticsCalendarDay {
  date: string;
  pnl: number;
  trade_count: number;
}

export interface AnalyticsHourCell {
  day_of_week: number;
  hour: number;
  pnl: number;
  trade_count: number;
}

export interface AnalyticsPieSlice {
  name: string;
  value: number;
  color?: string | null;
}

export interface AnalyticsLeaderboardEntry {
  rank: number;
  id: string;
  name: string;
  subtitle?: string | null;
  pnl: number;
  win_rate: number;
  profit_factor: number | null;
  trade_count: number;
  sharpe_ratio?: number | null;
}

export interface AnalyticsComparisonSeries {
  id: string;
  name: string;
  color: string;
  points: AnalyticsEquityPoint[];
}

export interface AnalyticsOverview {
  metrics: AnalyticsMetrics;
  equity_curve: AnalyticsEquityPoint[];
  drawdown: AnalyticsDrawdownPoint[];
  daily_returns: AnalyticsReturnPoint[];
  monthly_returns: AnalyticsReturnPoint[];
  calendar_heatmap: AnalyticsCalendarDay[];
  hour_heatmap: AnalyticsHourCell[];
  win_loss_pie: AnalyticsPieSlice[];
  symbol_pie: AnalyticsPieSlice[];
  strategy_pie: AnalyticsPieSlice[];
  account_leaderboard: AnalyticsLeaderboardEntry[];
  strategy_leaderboard: AnalyticsLeaderboardEntry[];
  comparison: AnalyticsComparisonSeries[];
}
