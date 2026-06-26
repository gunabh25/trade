import type {
  CalendarDay,
  EmotionStats,
  JournalEntry,
  JournalListResponse,
  JournalStats,
  JournalStrategy,
  StrategyPerformance,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import {
  toNullableNumber,
  toNullableString,
  toNumber,
  toString,
  toStringArray,
} from '@/lib/api/normalize';

function normalizeStrategy(raw: Record<string, unknown>): JournalStrategy {
  return {
    id: toString(raw.id),
    name: toString(raw.name),
    description: toNullableString(raw.description),
    symbols: toStringArray(raw.symbols),
    color: toNullableString(raw.color),
    rules: toNullableString(raw.rules),
    is_active: Boolean(raw.is_active),
    created_at: toString(raw.created_at),
  };
}

function normalizeEntry(raw: Record<string, unknown>): JournalEntry {
  const strategyRaw = raw.strategy;
  return {
    id: toString(raw.id),
    title: toString(raw.title),
    content: toNullableString(raw.content),
    notes: toNullableString(raw.notes),
    mood: toNullableString(raw.mood),
    session_date: toString(raw.session_date),
    pnl: toNullableNumber(raw.pnl),
    tags: toStringArray(raw.tags),
    emotions: toStringArray(raw.emotions),
    mistakes: toStringArray(raw.mistakes),
    lessons_learned: toNullableString(raw.lessons_learned),
    source: raw.source === 'auto_import' ? 'auto_import' : 'manual',
    symbol: toNullableString(raw.symbol),
    side: toNullableString(raw.side),
    quantity: raw.quantity != null ? toNumber(raw.quantity) : null,
    entry_price: toNullableNumber(raw.entry_price),
    exit_price: toNullableNumber(raw.exit_price),
    trade_id: toNullableString(raw.trade_id),
    strategy_id: toNullableString(raw.strategy_id),
    trading_account_id: toNullableString(raw.trading_account_id),
    strategy:
      strategyRaw && typeof strategyRaw === 'object'
        ? normalizeStrategy(strategyRaw as Record<string, unknown>)
        : null,
    screenshots: Array.isArray(raw.screenshots)
      ? raw.screenshots.map((item) => {
          const s = item as Record<string, unknown>;
          return {
            id: toString(s.id),
            file_url: toString(s.file_url),
            caption: toNullableString(s.caption),
            sort_order: toNumber(s.sort_order),
            created_at: toString(s.created_at),
          };
        })
      : [],
    created_at: toString(raw.created_at),
    updated_at: toString(raw.updated_at),
  };
}

function normalizeStats(raw: Record<string, unknown>): JournalStats {
  return {
    total_entries: toNumber(raw.total_entries),
    total_pnl: toNumber(raw.total_pnl),
    win_count: toNumber(raw.win_count),
    loss_count: toNumber(raw.loss_count),
    breakeven_count: toNumber(raw.breakeven_count),
    win_rate: toNumber(raw.win_rate),
    avg_win: toNumber(raw.avg_win),
    avg_loss: toNumber(raw.avg_loss),
    profit_factor: raw.profit_factor != null ? toNumber(raw.profit_factor) : null,
    best_trade: toNullableNumber(raw.best_trade),
    worst_trade: toNullableNumber(raw.worst_trade),
    avg_rr: raw.avg_rr != null ? toNumber(raw.avg_rr) : null,
  };
}

export interface JournalEntriesQuery {
  q?: string;
  strategy_id?: string;
  tag?: string;
  emotion?: string;
  page?: number;
  page_size?: number;
}

export async function listJournalEntries(
  query: JournalEntriesQuery = {},
): Promise<JournalListResponse> {
  const params = new URLSearchParams();
  if (query.q) params.set('q', query.q);
  if (query.strategy_id) params.set('strategy_id', query.strategy_id);
  if (query.tag) params.set('tag', query.tag);
  if (query.emotion) params.set('emotion', query.emotion);
  if (query.page) params.set('page', String(query.page));
  if (query.page_size) params.set('page_size', String(query.page_size));

  const qs = params.toString();
  const response = await apiRequest<Record<string, unknown>>(
    `/journal/entries${qs ? `?${qs}` : ''}`,
  );
  const data = response.data;
  const entriesRaw = Array.isArray(data.entries) ? data.entries : [];
  const paginationRaw = (data.pagination as Record<string, unknown> | undefined) ?? {};

  return {
    entries: entriesRaw.map((entry) => normalizeEntry(entry as Record<string, unknown>)),
    pagination: {
      page: toNumber(paginationRaw.page, 1),
      page_size: toNumber(paginationRaw.page_size, 20),
      total: toNumber(paginationRaw.total),
      total_pages: toNumber(paginationRaw.total_pages, 1),
    },
  };
}

export async function getJournalStats(): Promise<JournalStats> {
  const response = await apiRequest<Record<string, unknown>>('/journal/stats');
  return normalizeStats(response.data);
}

export async function getJournalCalendar(year: number, month: number): Promise<CalendarDay[]> {
  const response = await apiRequest<Record<string, unknown>[]>(
    `/journal/calendar?year=${String(year)}&month=${String(month)}`,
  );
  return response.data.map((day) => ({
    date: toString(day.date),
    pnl: toNumber(day.pnl),
    trade_count: toNumber(day.trade_count),
  }));
}

export async function listJournalStrategies(): Promise<JournalStrategy[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/strategies');
  return response.data.map((item) => normalizeStrategy(item));
}

export async function getStrategyPerformance(): Promise<StrategyPerformance[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/stats/by-strategy');
  return response.data.map((item) => ({
    strategy_id: toNullableString(item.strategy_id),
    strategy_name: toString(item.strategy_name),
    color: toNullableString(item.color),
    trade_count: toNumber(item.trade_count),
    total_pnl: toNumber(item.total_pnl),
    win_rate: toNumber(item.win_rate),
    avg_pnl: toNumber(item.avg_pnl),
  }));
}

export async function getEmotionStats(): Promise<EmotionStats[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/stats/emotions');
  return response.data.map((item) => ({
    emotion: toString(item.emotion),
    count: toNumber(item.count),
    total_pnl: toNumber(item.total_pnl),
    win_rate: toNumber(item.win_rate),
  }));
}

export async function listJournalTags(): Promise<string[]> {
  const response = await apiRequest<string[]>('/journal/tags');
  return response.data;
}

export async function getJournalEntry(entryId: string): Promise<JournalEntry> {
  const response = await apiRequest<Record<string, unknown>>(`/journal/entries/${entryId}`);
  return normalizeEntry(response.data);
}

export async function importJournalTrades(payload?: {
  trading_account_id?: string;
  since?: string;
}): Promise<{ imported: number; skipped: number }> {
  const response = await apiRequest<Record<string, unknown>>('/journal/import', {
    method: 'POST',
    body: payload ?? {},
  });
  return {
    imported: toNumber(response.data.imported),
    skipped: toNumber(response.data.skipped),
  };
}
