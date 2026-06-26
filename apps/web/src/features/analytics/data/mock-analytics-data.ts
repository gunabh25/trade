import type { AnalyticsOverview } from '@tradeflow/types/api';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function buildEquitySeries(): {
  equity: AnalyticsOverview['equity_curve'];
  drawdown: AnalyticsOverview['drawdown'];
} {
  const rand = seededRandom(42);
  let equity = 245_000;
  let peak = equity;
  const equity_curve: AnalyticsOverview['equity_curve'] = [];
  const drawdown: AnalyticsOverview['drawdown'] = [];

  for (let i = 0; i < 180; i++) {
    const d = new Date(2025, 11, 1);
    d.setDate(d.getDate() + i);
    const drift = (rand() - 0.42) * 2800;
    equity = Math.max(180_000, equity + drift);
    peak = Math.max(peak, equity);
    const dd = peak > 0 ? ((equity - peak) / peak) * 100 : 0;
    equity_curve.push({
      date: d.toISOString().slice(0, 10),
      equity: Math.round(equity * 100) / 100,
    });
    drawdown.push({
      date: d.toISOString().slice(0, 10),
      drawdown_pct: Math.round(dd * 100) / 100,
    });
  }

  return { equity: equity_curve, drawdown };
}

function buildCalendarHeatmap(): AnalyticsOverview['calendar_heatmap'] {
  const rand = seededRandom(99);
  const days: AnalyticsOverview['calendar_heatmap'] = [];
  for (let i = 0; i < 84; i++) {
    const d = new Date(2026, 3, 1);
    d.setDate(d.getDate() + i);
    const isWeekend = d.getDay() === 0 || d.getDay() === 6;
    if (isWeekend && rand() > 0.3) continue;
    const pnl = Math.round((rand() - 0.38) * 2400);
    days.push({
      date: d.toISOString().slice(0, 10),
      pnl,
      trade_count: Math.max(1, Math.floor(rand() * 8) + 1),
    });
  }
  return days;
}

function buildHourHeatmap(): AnalyticsOverview['hour_heatmap'] {
  const rand = seededRandom(7);
  const cells: AnalyticsOverview['hour_heatmap'] = [];
  for (let dow = 0; dow < 5; dow++) {
    for (let hour = 8; hour <= 16; hour++) {
      cells.push({
        day_of_week: dow,
        hour,
        pnl: Math.round((rand() - 0.4) * 1800),
        trade_count: Math.max(1, Math.floor(rand() * 12)),
      });
    }
  }
  return cells;
}

const { equity: equity_curve, drawdown } = buildEquitySeries();
const calendar_heatmap = buildCalendarHeatmap();

export const mockAnalyticsData: AnalyticsOverview = {
  metrics: {
    total_trades: 847,
    total_pnl: 39_750.42,
    win_count: 512,
    loss_count: 318,
    breakeven_count: 17,
    win_rate: 60.4,
    profit_factor: 2.18,
    expectancy: 46.93,
    average_r: 1.42,
    sharpe_ratio: 2.34,
    sortino_ratio: 3.12,
    max_drawdown_pct: -8.42,
    starting_equity: 245_000,
    ending_equity: 284_750.42,
  },
  equity_curve,
  drawdown,
  daily_returns: [
    { label: 'Mon', value: 842 },
    { label: 'Tue', value: -320 },
    { label: 'Wed', value: 1250 },
    { label: 'Thu', value: 680 },
    { label: 'Fri', value: -150 },
    { label: 'Sat', value: 0 },
    { label: 'Sun', value: 420 },
    { label: 'Mon', value: 910 },
    { label: 'Tue', value: 540 },
    { label: 'Wed', value: -780 },
    { label: 'Thu', value: 1120 },
    { label: 'Fri', value: 390 },
    { label: 'Mon', value: -210 },
    { label: 'Fri', value: 1560 },
  ],
  monthly_returns: [
    { label: 'Jul', value: 8200 },
    { label: 'Aug', value: 3200 },
    { label: 'Sep', value: -1800 },
    { label: 'Oct', value: 6400 },
    { label: 'Nov', value: 4500 },
    { label: 'Dec', value: 5750 },
    { label: 'Jan', value: 9100 },
    { label: 'Feb', value: 2800 },
    { label: 'Mar', value: -900 },
    { label: 'Apr', value: 5200 },
    { label: 'May', value: 6100 },
    { label: 'Jun', value: 4820 },
  ],
  calendar_heatmap,
  hour_heatmap: buildHourHeatmap(),
  win_loss_pie: [
    { name: 'Wins', value: 186_420, color: '#22c55e' },
    { name: 'Losses', value: 85_340, color: '#ef4444' },
  ],
  symbol_pie: [
    { name: 'ES', value: 42, color: '#22c55e' },
    { name: 'NQ', value: 28, color: '#3b82f6' },
    { name: 'CL', value: 12, color: '#f59e0b' },
    { name: 'GC', value: 8, color: '#a855f7' },
    { name: 'YM', value: 6, color: '#06b6d4' },
    { name: 'Other', value: 4, color: '#64748b' },
  ],
  strategy_pie: [
    { name: 'ORB Breakout', value: 38, color: '#22c55e' },
    { name: 'Mean Reversion', value: 24, color: '#3b82f6' },
    { name: 'Trend Following', value: 18, color: '#a855f7' },
    { name: 'Scalping', value: 12, color: '#f59e0b' },
    { name: 'Other', value: 8, color: '#64748b' },
  ],
  account_leaderboard: [
    {
      rank: 1,
      id: 'acc-1',
      name: 'Primary — Apex',
      subtitle: 'leader',
      pnl: 18_420,
      win_rate: 64.2,
      profit_factor: 2.45,
      trade_count: 312,
      sharpe_ratio: 2.8,
    },
    {
      rank: 2,
      id: 'acc-2',
      name: 'Prop Alpha',
      subtitle: 'follower',
      pnl: 12_850,
      win_rate: 58.1,
      profit_factor: 1.92,
      trade_count: 248,
      sharpe_ratio: 2.1,
    },
    {
      rank: 3,
      id: 'acc-3',
      name: 'Futures Desk',
      subtitle: 'leader',
      pnl: 5_920,
      win_rate: 55.8,
      profit_factor: 1.68,
      trade_count: 156,
      sharpe_ratio: 1.74,
    },
    {
      rank: 4,
      id: 'acc-4',
      name: 'Paper Sim',
      subtitle: 'follower',
      pnl: 2_560,
      win_rate: 52.3,
      profit_factor: 1.35,
      trade_count: 131,
      sharpe_ratio: 1.2,
    },
  ],
  strategy_leaderboard: [
    {
      rank: 1,
      id: 's1',
      name: 'Opening Range Breakout',
      subtitle: '2 symbols',
      pnl: 22_400,
      win_rate: 67.5,
      profit_factor: 2.82,
      trade_count: 198,
    },
    {
      rank: 2,
      id: 's2',
      name: 'Mean Reversion',
      subtitle: '2 symbols',
      pnl: 9_120,
      win_rate: 56.2,
      profit_factor: 1.74,
      trade_count: 164,
    },
    {
      rank: 3,
      id: 's3',
      name: 'Trend Following',
      subtitle: '2 symbols',
      pnl: 5_680,
      win_rate: 51.8,
      profit_factor: 1.52,
      trade_count: 142,
    },
    {
      rank: 4,
      id: 's4',
      name: 'Scalping',
      subtitle: '3 symbols',
      pnl: 2_350,
      win_rate: 48.9,
      profit_factor: 1.21,
      trade_count: 343,
    },
  ],
  comparison: [
    {
      id: 'acc-1',
      name: 'Primary — Apex',
      color: '#22c55e',
      points: equity_curve
        .filter((_, i) => i % 6 === 0)
        .map((p, i) => ({
          ...p,
          equity: 245_000 + i * 220 + Math.sin(i) * 1200,
        })),
    },
    {
      id: 'acc-2',
      name: 'Prop Alpha',
      color: '#3b82f6',
      points: equity_curve
        .filter((_, i) => i % 6 === 0)
        .map((p, i) => ({
          ...p,
          equity: 245_000 + i * 160 + Math.cos(i) * 900,
        })),
    },
    {
      id: 'acc-3',
      name: 'Futures Desk',
      color: '#a855f7',
      points: equity_curve
        .filter((_, i) => i % 6 === 0)
        .map((p, i) => ({
          ...p,
          equity: 245_000 + i * 90 + Math.sin(i * 0.7) * 600,
        })),
    },
  ],
};

export { DAY_LABELS };

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number, digits = 1): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(digits)}%`;
}

export function formatRatio(value: number | null | undefined, digits = 2): string {
  if (value == null) return '—';
  return value.toFixed(digits);
}

export function formatCompactDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
