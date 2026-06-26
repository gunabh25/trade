'use client';

import { BookOpen } from 'lucide-react';
import { useRef, useState } from 'react';

import { Button, cn } from '@tradeflow/ui';

import { DashboardSkeleton } from '@/features/dashboard/components/dashboard-skeleton';
import {
  FadeInItem,
  FadeInStagger,
  EmptyState,
} from '@/features/dashboard/components/motion-primitives';
import {
  EmotionPerformanceChart,
  JournalCalendar,
  MistakeStatsChart,
  StrategyPerformanceChart,
  SymbolPerformanceChart,
  WeekdayPerformanceChart,
} from '@/features/journal/components/journal-charts';
import { JournalEntryDetail } from '@/features/journal/components/journal-entry-detail';
import { JournalEntryForm } from '@/features/journal/components/journal-entry-form';
import { JournalEntryList } from '@/features/journal/components/journal-entry-list';
import { JournalFilters } from '@/features/journal/components/journal-filters';
import { JournalStatsBar } from '@/features/journal/components/journal-stats-bar';
import { JournalTimeline } from '@/features/journal/components/journal-timeline';
import { useJournalData } from '@/features/journal/hooks/use-journal-data';
import { useJournalKeyboardShortcuts } from '@/features/journal/hooks/use-journal-keyboard';

import type { JournalEntry } from '@tradeflow/types/api';

const VIEWS = [
  { id: 'log' as const, label: 'Trade Log' },
  { id: 'timeline' as const, label: 'Timeline' },
  { id: 'analytics' as const, label: 'Analytics' },
];

export function JournalPage() {
  const data = useJournalData();
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<JournalEntry | null>(null);

  useJournalKeyboardShortcuts({
    onSearch: () => searchInputRef.current?.focus(),
    onNewEntry: () => {
      setEditingEntry(null);
      setFormOpen(true);
    },
    onImport: () => void data.importTrades(),
    onExportCsv: () => {
      void import('@/features/journal/api/journal-api').then(({ downloadJournalExport }) =>
        downloadJournalExport('csv', {
          ...(data.search ? { q: data.search } : {}),
          ...(data.selectedStrategy ? { strategy_id: data.selectedStrategy } : {}),
          ...(data.selectedTag ? { tag: data.selectedTag } : {}),
          ...(data.selectedEmotion ? { emotion: data.selectedEmotion } : {}),
        }),
      );
    },
    onNavigatePrev: () => {
      data.navigateEntry('prev');
    },
    onNavigateNext: () => {
      data.navigateEntry('next');
    },
    enabled: !formOpen,
  });

  if (data.loading) {
    return <DashboardSkeleton />;
  }

  if (data.error) {
    return (
      <div className="p-4 sm:p-6">
        <EmptyState
          icon={BookOpen}
          title="Could not load journal"
          description={data.error}
          action={
            <Button size="sm" onClick={() => void data.refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <>
      <FadeInStagger className="space-y-6 p-4 sm:p-6">
        <FadeInItem>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <BookOpen className="text-primary h-5 w-5" />
                <h1 className="text-xl font-semibold tracking-tight">Trading Journal</h1>
              </div>
              <p className="text-muted-foreground mt-1 text-sm">
                Review trades, track emotions, and improve with data-driven insights
              </p>
            </div>
            <p className="text-muted-foreground hidden text-xs xl:block">
              Shortcuts: / search · n new · i import · j/k navigate · ⌘e export
            </p>
          </div>
        </FadeInItem>

        <FadeInItem>
          <JournalStatsBar stats={data.stats} />
        </FadeInItem>

        <FadeInItem>
          <JournalFilters
            data={data}
            searchInputRef={searchInputRef}
            onNewEntry={() => {
              setEditingEntry(null);
              setFormOpen(true);
            }}
            onImport={() => void data.importTrades()}
            importing={data.importing}
          />
        </FadeInItem>

        <FadeInItem>
          <div className="border-border/60 bg-card/50 flex gap-1 rounded-lg border p-1">
            {VIEWS.map((view) => (
              <button
                key={view.id}
                type="button"
                onClick={() => {
                  data.setActiveView(view.id);
                }}
                className={cn(
                  'flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors sm:flex-none',
                  data.activeView === view.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {view.label}
              </button>
            ))}
          </div>
        </FadeInItem>

        {data.activeView === 'log' ? (
          <FadeInItem className="grid gap-4 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <JournalEntryList
                entries={data.entries}
                selectedId={data.selectedEntry?.id ?? null}
                onSelect={data.setSelectedEntry}
              />
            </div>
            <div className="lg:col-span-3">
              <JournalEntryDetail
                entry={data.selectedEntry}
                onEdit={(entry) => {
                  setEditingEntry(entry);
                  setFormOpen(true);
                }}
                onUpdated={data.upsertEntry}
              />
            </div>
          </FadeInItem>
        ) : null}

        {data.activeView === 'timeline' ? (
          <FadeInItem className="grid gap-4 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <JournalTimeline
                entries={data.entries}
                selectedId={data.selectedEntry?.id ?? null}
                onSelect={data.setSelectedEntry}
              />
            </div>
            <div className="lg:col-span-3">
              <JournalEntryDetail
                entry={data.selectedEntry}
                onEdit={(entry) => {
                  setEditingEntry(entry);
                  setFormOpen(true);
                }}
                onUpdated={data.upsertEntry}
              />
            </div>
          </FadeInItem>
        ) : null}

        {data.activeView === 'analytics' ? (
          <FadeInItem className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <JournalCalendar data={data.calendar} />
            <StrategyPerformanceChart data={data.strategyPerformance} />
            <WeekdayPerformanceChart data={data.weekdayPerformance} />
            <SymbolPerformanceChart data={data.symbolPerformance} />
            <EmotionPerformanceChart data={data.emotionStats} />
            <MistakeStatsChart data={data.mistakeStats} />
          </FadeInItem>
        ) : null}
      </FadeInStagger>

      <JournalEntryForm
        open={formOpen}
        onOpenChange={setFormOpen}
        strategies={data.strategies}
        existingTags={data.tags}
        entry={editingEntry}
        onSaved={(entry) => {
          data.upsertEntry(entry);
          void data.refetch();
        }}
      />
    </>
  );
}
