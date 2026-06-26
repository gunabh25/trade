import type {
  CalendarDay,
  EmotionStats,
  JournalEntry,
  JournalStats,
  JournalStrategy,
  StrategyPerformance,
} from '@tradeflow/types/api';

export const EMOTIONS = [
  'confident',
  'calm',
  'fomo',
  'fearful',
  'revenge',
  'impatient',
  'disciplined',
  'anxious',
] as const;

export const MOCK_STRATEGIES: JournalStrategy[] = [
  {
    id: 's1',
    name: 'Opening Range Breakout',
    description: 'Trade the first 30-min range break with volume confirmation',
    symbols: ['ES', 'NQ'],
    color: '#22c55e',
    rules: 'Only trade if range > 8 pts. Stop at range midpoint.',
    is_active: true,
    created_at: '2026-01-15T10:00:00Z',
  },
  {
    id: 's2',
    name: 'Mean Reversion',
    description: 'Fade extended moves at key VWAP levels',
    symbols: ['ES', 'CL'],
    color: '#3b82f6',
    rules: 'Max 2 contracts. Exit at VWAP touch.',
    is_active: true,
    created_at: '2026-02-01T10:00:00Z',
  },
  {
    id: 's3',
    name: 'Trend Following',
    description: 'Pullback entries in established trends',
    symbols: ['NQ', 'YM'],
    color: '#a855f7',
    rules: null,
    is_active: true,
    created_at: '2026-03-10T10:00:00Z',
  },
];

export const MOCK_ENTRIES: JournalEntry[] = [
  {
    id: 'e1',
    title: 'ES Long — ORB Breakout',
    content: 'Clean breakout above opening range high with strong volume.',
    notes: 'Entered on retest of broken level. Held through lunch consolidation.',
    mood: 'focused',
    session_date: '2026-06-24',
    pnl: 875,
    tags: ['breakout', 'morning', 'es'],
    emotions: ['confident', 'disciplined'],
    mistakes: [],
    lessons_learned: 'Patience on retest entry paid off — avoid chasing initial break.',
    source: 'manual',
    symbol: 'ES',
    side: 'long',
    quantity: 3,
    entry_price: 5520.5,
    exit_price: 5532.25,
    trade_id: null,
    strategy_id: 's1',
    trading_account_id: null,
    strategy: MOCK_STRATEGIES[0] ?? null,
    screenshots: [],
    created_at: '2026-06-24T16:30:00Z',
    updated_at: '2026-06-24T16:30:00Z',
  },
  {
    id: 'e2',
    title: 'NQ Short — Failed Breakout',
    content: 'Shorted failed breakout above overnight high.',
    notes: 'Revenge trade after morning loss. Should have stopped for the day.',
    mood: 'frustrated',
    session_date: '2026-06-23',
    pnl: -420,
    tags: ['reversal', 'mistake'],
    emotions: ['revenge', 'impatient'],
    mistakes: ['revenge trading', 'oversized position', 'ignored daily loss limit'],
    lessons_learned: 'Stop trading after 2 consecutive losses. Size down on revenge setups.',
    source: 'manual',
    symbol: 'NQ',
    side: 'short',
    quantity: 2,
    entry_price: 20150,
    exit_price: 20171,
    trade_id: null,
    strategy_id: 's2',
    trading_account_id: null,
    strategy: MOCK_STRATEGIES[1] ?? null,
    screenshots: [],
    created_at: '2026-06-23T15:00:00Z',
    updated_at: '2026-06-23T15:00:00Z',
  },
  {
    id: 'e3',
    title: 'ES Long — Trend Pullback',
    content: 'Pullback to 20 EMA in uptrend. Textbook entry.',
    notes: null,
    mood: 'calm',
    session_date: '2026-06-22',
    pnl: 1250,
    tags: ['trend', 'pullback'],
    emotions: ['calm', 'confident'],
    mistakes: [],
    lessons_learned: null,
    source: 'auto_import',
    symbol: 'ES',
    side: 'long',
    quantity: 4,
    entry_price: 5498,
    exit_price: 5512.5,
    trade_id: null,
    strategy_id: 's3',
    trading_account_id: null,
    strategy: MOCK_STRATEGIES[2] ?? null,
    screenshots: [],
    created_at: '2026-06-22T14:00:00Z',
    updated_at: '2026-06-22T14:00:00Z',
  },
  {
    id: 'e4',
    title: 'CL Short — News Fade',
    content: 'Faded inventory report spike.',
    notes: 'News trade — usually avoid but setup was clear.',
    mood: 'anxious',
    session_date: '2026-06-20',
    pnl: 310,
    tags: ['news', 'cl'],
    emotions: ['anxious', 'fomo'],
    mistakes: ['traded during news without plan'],
    lessons_learned: 'Pre-define news trade rules or skip entirely.',
    source: 'manual',
    symbol: 'CL',
    side: 'short',
    quantity: 1,
    entry_price: 78.45,
    exit_price: 77.92,
    trade_id: null,
    strategy_id: 's2',
    trading_account_id: null,
    strategy: MOCK_STRATEGIES[1] ?? null,
    screenshots: [],
    created_at: '2026-06-20T13:00:00Z',
    updated_at: '2026-06-20T13:00:00Z',
  },
  {
    id: 'e5',
    title: 'ES Scalp — Lunch Chop',
    content: 'Small scalp during lunch range.',
    notes: null,
    mood: 'neutral',
    session_date: '2026-06-19',
    pnl: -125,
    tags: ['scalp', 'lunch'],
    emotions: ['impatient'],
    mistakes: ['traded lunch chop'],
    lessons_learned: 'No trades between 12:00-13:30 ET.',
    source: 'auto_import',
    symbol: 'ES',
    side: 'long',
    quantity: 1,
    entry_price: 5510,
    exit_price: 5507.5,
    trade_id: null,
    strategy_id: null,
    trading_account_id: null,
    strategy: null,
    screenshots: [],
    created_at: '2026-06-19T17:00:00Z',
    updated_at: '2026-06-19T17:00:00Z',
  },
];

export const MOCK_STATS: JournalStats = {
  total_entries: 5,
  total_pnl: 1890,
  win_count: 3,
  loss_count: 2,
  breakeven_count: 0,
  win_rate: 60,
  avg_win: 811.67,
  avg_loss: 272.5,
  profit_factor: 4.46,
  best_trade: 1250,
  worst_trade: -420,
  avg_rr: 2.98,
};

export const MOCK_CALENDAR: CalendarDay[] = [
  { date: '2026-06-02', pnl: 320, trade_count: 2 },
  { date: '2026-06-03', pnl: -180, trade_count: 1 },
  { date: '2026-06-04', pnl: 540, trade_count: 3 },
  { date: '2026-06-05', pnl: 0, trade_count: 0 },
  { date: '2026-06-06', pnl: 890, trade_count: 2 },
  { date: '2026-06-09', pnl: -250, trade_count: 2 },
  { date: '2026-06-10', pnl: 410, trade_count: 1 },
  { date: '2026-06-11', pnl: 120, trade_count: 1 },
  { date: '2026-06-12', pnl: -90, trade_count: 1 },
  { date: '2026-06-13', pnl: 670, trade_count: 2 },
  { date: '2026-06-16', pnl: -310, trade_count: 2 },
  { date: '2026-06-17', pnl: 230, trade_count: 1 },
  { date: '2026-06-18', pnl: 450, trade_count: 2 },
  { date: '2026-06-19', pnl: -125, trade_count: 1 },
  { date: '2026-06-20', pnl: 310, trade_count: 1 },
  { date: '2026-06-22', pnl: 1250, trade_count: 1 },
  { date: '2026-06-23', pnl: -420, trade_count: 1 },
  { date: '2026-06-24', pnl: 875, trade_count: 1 },
];

export const MOCK_STRATEGY_PERF: StrategyPerformance[] = [
  {
    strategy_id: 's1',
    strategy_name: 'Opening Range Breakout',
    color: '#22c55e',
    trade_count: 12,
    total_pnl: 3420,
    win_rate: 66.7,
    avg_pnl: 285,
  },
  {
    strategy_id: 's3',
    strategy_name: 'Trend Following',
    color: '#a855f7',
    trade_count: 8,
    total_pnl: 2100,
    win_rate: 62.5,
    avg_pnl: 262.5,
  },
  {
    strategy_id: 's2',
    strategy_name: 'Mean Reversion',
    color: '#3b82f6',
    trade_count: 15,
    total_pnl: -530,
    win_rate: 40,
    avg_pnl: -35.33,
  },
  {
    strategy_id: null,
    strategy_name: 'Unassigned',
    color: '#64748b',
    trade_count: 5,
    total_pnl: -100,
    win_rate: 40,
    avg_pnl: -20,
  },
];

export const MOCK_EMOTION_STATS: EmotionStats[] = [
  { emotion: 'confident', count: 8, total_pnl: 4200, win_rate: 75 },
  { emotion: 'disciplined', count: 6, total_pnl: 3100, win_rate: 83.3 },
  { emotion: 'calm', count: 5, total_pnl: 1800, win_rate: 60 },
  { emotion: 'revenge', count: 3, total_pnl: -890, win_rate: 0 },
  { emotion: 'impatient', count: 4, total_pnl: -420, win_rate: 25 },
  { emotion: 'anxious', count: 2, total_pnl: 310, win_rate: 50 },
];

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function filterEntries(
  entries: JournalEntry[],
  query: string,
  tag: string | null,
  strategyId: string | null,
): JournalEntry[] {
  return entries.filter((entry) => {
    if (strategyId && entry.strategy_id !== strategyId) return false;
    if (tag && !entry.tags?.includes(tag)) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      entry.title.toLowerCase().includes(q) ||
      (entry.symbol?.toLowerCase().includes(q) ?? false) ||
      (entry.notes?.toLowerCase().includes(q) ?? false) ||
      (entry.content?.toLowerCase().includes(q) ?? false) ||
      (entry.tags?.some((t) => t.toLowerCase().includes(q)) ?? false) ||
      (entry.lessons_learned?.toLowerCase().includes(q) ?? false)
    );
  });
}

export function getAllTags(entries: JournalEntry[]): string[] {
  const tags = new Set<string>();
  for (const entry of entries) {
    entry.tags?.forEach((t) => tags.add(t));
  }
  return [...tags].sort();
}
