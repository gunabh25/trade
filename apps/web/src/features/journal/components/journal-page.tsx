'use client';

import { BookOpen } from 'lucide-react';

import { FadeInItem, FadeInStagger } from '@/features/dashboard/components/motion-primitives';
import {
  JournalCalendar,
  EmotionPerformanceChart,
  StrategyPerformanceChart,
} from '@/features/journal/components/journal-charts';
import { JournalEntryDetail } from '@/features/journal/components/journal-entry-detail';
import { JournalEntryList } from '@/features/journal/components/journal-entry-list';
import { JournalFilters } from '@/features/journal/components/journal-filters';
import { JournalStatsBar } from '@/features/journal/components/journal-stats-bar';
import { useJournalData } from '@/features/journal/hooks/use-journal-data';

export function JournalPage() {
  const data = useJournalData();

  return (
    <FadeInStagger className="space-y-6 p-4 sm:p-6">
      <FadeInItem>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="text-primary h-5 w-5" />
              <h1 className="text-xl font-semibold tracking-tight">Trading Journal</h1>
            </div>
            <p className="text-muted-foreground mt-1 text-sm">
              Review trades, track emotions, and improve with data-driven insights
            </p>
          </div>
        </div>
      </FadeInItem>

      <FadeInItem>
        <JournalStatsBar stats={data.stats} />
      </FadeInItem>

      <FadeInItem>
        <JournalFilters data={data} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <JournalEntryList
            entries={data.entries}
            selectedId={data.selectedEntry?.id ?? null}
            onSelect={data.setSelectedEntry}
          />
        </div>
        <div className="lg:col-span-3">
          <JournalEntryDetail entry={data.selectedEntry} />
        </div>
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <JournalCalendar data={data.calendar} />
        <StrategyPerformanceChart data={data.strategyPerformance} />
        <div className="md:col-span-2 xl:col-span-1">
          <EmotionPerformanceChart data={data.emotionStats} />
        </div>
      </FadeInItem>
    </FadeInStagger>
  );
}
