'use client';

import { useMemo, useState } from 'react';

import type { JournalEntry } from '@tradeflow/types/api';

import {
  MOCK_CALENDAR,
  MOCK_EMOTION_STATS,
  MOCK_ENTRIES,
  MOCK_STATS,
  MOCK_STRATEGIES,
  MOCK_STRATEGY_PERF,
  filterEntries,
  getAllTags,
} from '@/features/journal/data/mock-journal-data';

export function useJournalData() {
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [calendarMonth, setCalendarMonth] = useState({ year: 2026, month: 6 });

  const entries = useMemo(
    () => filterEntries(MOCK_ENTRIES, search, selectedTag, selectedStrategy),
    [search, selectedTag, selectedStrategy],
  );

  const tags = useMemo(() => getAllTags(MOCK_ENTRIES), []);

  return {
    loading: false,
    entries,
    allEntries: MOCK_ENTRIES,
    stats: MOCK_STATS,
    calendar: MOCK_CALENDAR,
    strategies: MOCK_STRATEGIES,
    strategyPerformance: MOCK_STRATEGY_PERF,
    emotionStats: MOCK_EMOTION_STATS,
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
