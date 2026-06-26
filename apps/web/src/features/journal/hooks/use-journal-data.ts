'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import type {
  CalendarDay,
  EmotionStats,
  JournalEntry,
  JournalStats,
  JournalStrategy,
  StrategyPerformance,
} from '@tradeflow/types/api';

import {
  getEmotionStats,
  getJournalCalendar,
  getJournalStats,
  getStrategyPerformance,
  listJournalEntries,
  listJournalStrategies,
  listJournalTags,
  type JournalEntriesQuery,
} from '@/features/journal/api/journal-api';
import { ApiClientError } from '@/lib/errors';

const EMPTY_STATS: JournalStats = {
  total_entries: 0,
  total_pnl: 0,
  win_count: 0,
  loss_count: 0,
  breakeven_count: 0,
  win_rate: 0,
  avg_win: 0,
  avg_loss: 0,
  profit_factor: null,
  best_trade: null,
  worst_trade: null,
  avg_rr: null,
};

export function useJournalData() {
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() + 1 };
  });

  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [stats, setStats] = useState<JournalStats>(EMPTY_STATS);
  const [calendar, setCalendar] = useState<CalendarDay[]>([]);
  const [strategies, setStrategies] = useState<JournalStrategy[]>([]);
  const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([]);
  const [emotionStats, setEmotionStats] = useState<EmotionStats[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const entriesQuery: JournalEntriesQuery = { page_size: 100 };
      if (search) entriesQuery.q = search;
      if (selectedTag) entriesQuery.tag = selectedTag;
      if (selectedStrategy) entriesQuery.strategy_id = selectedStrategy;

      const [
        entriesResult,
        statsResult,
        calendarResult,
        strategiesResult,
        perfResult,
        emotionsResult,
        tagsResult,
      ] = await Promise.all([
        listJournalEntries(entriesQuery),
        getJournalStats(),
        getJournalCalendar(calendarMonth.year, calendarMonth.month),
        listJournalStrategies(),
        getStrategyPerformance(),
        getEmotionStats(),
        listJournalTags(),
      ]);

      setEntries(entriesResult.entries);
      setStats(statsResult);
      setCalendar(calendarResult);
      setStrategies(strategiesResult);
      setStrategyPerformance(perfResult);
      setEmotionStats(emotionsResult);
      setTags(tagsResult);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load journal');
    } finally {
      setLoading(false);
    }
  }, [calendarMonth.month, calendarMonth.year, search, selectedStrategy, selectedTag]);

  useEffect(() => {
    const timer = setTimeout(
      () => {
        void load();
      },
      search ? 300 : 0,
    );
    return () => {
      clearTimeout(timer);
    };
  }, [load, search]);

  useEffect(() => {
    if (entries.length === 0) {
      setSelectedEntry(null);
      return;
    }
    setSelectedEntry((current) => {
      if (current && entries.some((entry) => entry.id === current.id)) {
        return current;
      }
      return entries[0] ?? null;
    });
  }, [entries]);

  const filteredEntries = useMemo(() => entries, [entries]);

  return {
    loading,
    error,
    refetch: load,
    entries: filteredEntries,
    allEntries: entries,
    stats,
    calendar,
    strategies,
    strategyPerformance,
    emotionStats,
    tags,
    search,
    setSearch,
    selectedTag,
    setSelectedTag,
    selectedStrategy,
    setSelectedStrategy,
    selectedEntry,
    setSelectedEntry,
    calendarMonth,
    setCalendarMonth,
  };
}

export type JournalData = ReturnType<typeof useJournalData>;
