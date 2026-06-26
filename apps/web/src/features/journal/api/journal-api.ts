import type {
  CalendarDay,
  CreateJournalEntryPayload,
  EmotionStats,
  JournalEntry,
  JournalListResponse,
  JournalStats,
  JournalStrategy,
  MistakeStats,
  StrategyPerformance,
  SymbolPerformance,
  WeekdayPerformance,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import {
  toNullableNumber,
  toNullableString,
  toNumber,
  toString,
  toStringArray,
} from '@/lib/api/normalize';

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

function getCsrfToken(): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const match = /(?:^|; )tf_csrf=([^;]*)/.exec(document.cookie);
  return match?.[1] ? decodeURIComponent(match[1]) : undefined;
}

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

export function normalizeEntry(raw: Record<string, unknown>): JournalEntry {
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
    grade: raw.grade != null ? toNumber(raw.grade) : null,
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
  symbol?: string;
  tag?: string;
  emotion?: string;
  page?: number;
  page_size?: number;
}

function buildQueryString(query: JournalEntriesQuery): string {
  const params = new URLSearchParams();
  if (query.q) params.set('q', query.q);
  if (query.strategy_id) params.set('strategy_id', query.strategy_id);
  if (query.symbol) params.set('symbol', query.symbol);
  if (query.tag) params.set('tag', query.tag);
  if (query.emotion) params.set('emotion', query.emotion);
  if (query.page) params.set('page', String(query.page));
  if (query.page_size) params.set('page_size', String(query.page_size));
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

export async function listJournalEntries(
  query: JournalEntriesQuery = {},
): Promise<JournalListResponse> {
  const response = await apiRequest<Record<string, unknown>>(
    `/journal/entries${buildQueryString(query)}`,
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

export async function getWeekdayPerformance(): Promise<WeekdayPerformance[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/stats/by-weekday');
  return response.data.map((item) => ({
    weekday: toString(item.weekday),
    weekday_index: toNumber(item.weekday_index),
    trade_count: toNumber(item.trade_count),
    total_pnl: toNumber(item.total_pnl),
    win_rate: toNumber(item.win_rate),
  }));
}

export async function getSymbolPerformance(): Promise<SymbolPerformance[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/stats/by-symbol');
  return response.data.map((item) => ({
    symbol: toString(item.symbol),
    trade_count: toNumber(item.trade_count),
    total_pnl: toNumber(item.total_pnl),
    win_rate: toNumber(item.win_rate),
    avg_pnl: toNumber(item.avg_pnl),
  }));
}

export async function getMistakeStats(): Promise<MistakeStats[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/journal/stats/mistakes');
  return response.data.map((item) => ({
    mistake: toString(item.mistake),
    count: toNumber(item.count),
    total_pnl: toNumber(item.total_pnl),
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

export async function createJournalEntry(
  payload: CreateJournalEntryPayload,
): Promise<JournalEntry> {
  const response = await apiRequest<Record<string, unknown>>('/journal/entries', {
    method: 'POST',
    body: payload,
  });
  return normalizeEntry(response.data);
}

export async function updateJournalEntry(
  entryId: string,
  payload: Partial<CreateJournalEntryPayload>,
): Promise<JournalEntry> {
  const response = await apiRequest<Record<string, unknown>>(`/journal/entries/${entryId}`, {
    method: 'PUT',
    body: payload,
  });
  return normalizeEntry(response.data);
}

export async function deleteJournalEntry(entryId: string): Promise<void> {
  await apiRequest(`/journal/entries/${entryId}`, { method: 'DELETE' });
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

export async function uploadJournalScreenshot(
  entryId: string,
  file: File,
  caption?: string,
): Promise<JournalEntry> {
  const formData = new FormData();
  formData.append('file', file);
  if (caption) formData.append('caption', caption);

  const csrf = getCsrfToken();
  const headers = new Headers();
  if (csrf) headers.set('X-CSRF-Token', csrf);

  const response = await fetch(
    `${getApiBaseUrl()}/api/${getApiVersion()}/journal/entries/${entryId}/screenshots/upload`,
    {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers,
    },
  );

  if (!response.ok) {
    throw new Error('Failed to upload screenshot');
  }

  const body = (await response.json()) as { data?: Record<string, unknown> };
  if (body.data) {
    return normalizeEntry(body.data);
  }
  return getJournalEntry(entryId);
}

export async function downloadJournalExport(
  format: 'csv' | 'pdf',
  query: JournalEntriesQuery = {},
): Promise<void> {
  const url = `${getApiBaseUrl()}/api/${getApiVersion()}/journal/export/${format}${buildQueryString(query)}`;
  const response = await fetch(url, { credentials: 'include' });
  if (!response.ok) throw new Error(`Export failed (${String(response.status)})`);

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = `journal-export.${format}`;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export function getScreenshotUrl(fileUrl: string): string {
  if (fileUrl.startsWith('http')) return fileUrl;
  return `${getApiBaseUrl()}${fileUrl}`;
}
