'use client';

import { CalendarDays } from 'lucide-react';
import { useMemo } from 'react';

import type { JournalEntry } from '@tradeflow/types/api';

import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  cn,
} from '@tradeflow/ui';

import { formatCurrency, formatGrade } from '@/features/journal/utils/format';

interface JournalTimelineProps {
  entries: JournalEntry[];
  selectedId: string | null;
  onSelect: (entry: JournalEntry) => void;
}

export function JournalTimeline({ entries, selectedId, onSelect }: JournalTimelineProps) {
  const grouped = useMemo(() => {
    const map = new Map<string, JournalEntry[]>();
    const sorted = [...entries].sort(
      (a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime(),
    );
    for (const entry of sorted) {
      const key = entry.session_date;
      const list = map.get(key) ?? [];
      list.push(entry);
      map.set(key, list);
    }
    return [...map.entries()];
  }, [entries]);

  if (entries.length === 0) {
    return (
      <Card className="border-border/60 bg-card/80 shadow-none">
        <CardContent className="text-muted-foreground flex flex-col items-center py-12 text-sm">
          <CalendarDays className="mb-3 h-8 w-8 opacity-40" />
          No entries for timeline view
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Timeline</CardTitle>
        <CardDescription>Chronological trade history</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {grouped.map(([date, dayEntries]) => (
          <div key={date}>
            <p className="text-muted-foreground mb-3 text-xs font-semibold uppercase tracking-wider">
              {new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {
                weekday: 'long',
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </p>
            <div className="border-border/60 relative space-y-3 border-l pl-4">
              {dayEntries.map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => {
                    onSelect(entry);
                  }}
                  className={cn(
                    'hover:bg-accent/40 relative w-full rounded-lg border px-4 py-3 text-left transition-colors',
                    selectedId === entry.id
                      ? 'border-primary/40 bg-accent/60'
                      : 'border-border/60 bg-card/50',
                  )}
                >
                  <span className="bg-primary absolute -left-[21px] top-4 h-2.5 w-2.5 rounded-full" />
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{entry.title}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {entry.symbol ? (
                          <span className="text-muted-foreground text-xs">{entry.symbol}</span>
                        ) : null}
                        {entry.strategy ? (
                          <Badge variant="outline" className="text-[10px]">
                            {entry.strategy.name}
                          </Badge>
                        ) : null}
                        {entry.grade ? (
                          <span className="text-xs text-amber-400">{formatGrade(entry.grade)}</span>
                        ) : null}
                      </div>
                    </div>
                    {entry.pnl !== null ? (
                      <span
                        className={cn(
                          'shrink-0 text-sm font-semibold tabular-nums',
                          entry.pnl >= 0 ? 'text-profit' : 'text-loss',
                        )}
                      >
                        {entry.pnl >= 0 ? '+' : ''}
                        {formatCurrency(entry.pnl)}
                      </span>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
