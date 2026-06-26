export type JournalSource = 'manual' | 'auto_import';

export interface JournalStrategy {
  id: string;
  name: string;
  description: string | null;
  symbols: string[] | null;
  color: string | null;
  rules: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JournalScreenshot {
  id: string;
  file_url: string;
  caption: string | null;
  sort_order: number;
  created_at: string;
}

export interface JournalEntry {
  id: string;
  title: string;
  content: string | null;
  notes: string | null;
  mood: string | null;
  session_date: string;
  pnl: number | null;
  tags: string[] | null;
  emotions: string[] | null;
  mistakes: string[] | null;
  lessons_learned: string | null;
  source: JournalSource;
  symbol: string | null;
  side: string | null;
  quantity: number | null;
  entry_price: number | null;
  exit_price: number | null;
  trade_id: string | null;
  strategy_id: string | null;
  trading_account_id: string | null;
  strategy: JournalStrategy | null;
  screenshots: JournalScreenshot[];
  created_at: string;
  updated_at: string;
}

export interface JournalStats {
  total_entries: number;
  total_pnl: number;
  win_count: number;
  loss_count: number;
  breakeven_count: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number | null;
  best_trade: number | null;
  worst_trade: number | null;
  avg_rr: number | null;
}

export interface CalendarDay {
  date: string;
  pnl: number;
  trade_count: number;
}

export interface StrategyPerformance {
  strategy_id: string | null;
  strategy_name: string;
  color: string | null;
  trade_count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
}

export interface EmotionStats {
  emotion: string;
  count: number;
  total_pnl: number;
  win_rate: number;
}

export interface JournalListResponse {
  entries: JournalEntry[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}
