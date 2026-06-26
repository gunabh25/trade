'use client';

import { BookOpen, Camera, ChevronRight } from 'lucide-react';

import type { JournalEntry } from '@tradeflow/types/api';

import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  ScrollArea,
  cn,
} from '@tradeflow/ui';

import { formatCurrency, formatGrade } from '@/features/journal/utils/format';

interface JournalEntryListProps {
  entries: JournalEntry[];
  selectedId: string | null;
  onSelect: (entry: JournalEntry) => void;
}

export function JournalEntryList({ entries, selectedId, onSelect }: JournalEntryListProps) {
  if (entries.length === 0) {
    return (
      <Card className="border-border/60 bg-card/80 shadow-none">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <BookOpen className="text-muted-foreground mb-3 h-8 w-8" />
          <p className="text-sm font-medium">No entries found</p>
          <p className="text-muted-foreground mt-1 text-xs">Try adjusting your filters</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Trade Log</CardTitle>
        <CardDescription>{entries.length} entries</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[420px] md:h-[520px]">
          <div className="divide-border/60 divide-y">
            {entries.map((entry) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => {
                  onSelect(entry);
                }}
                className={cn(
                  'hover:bg-accent/40 flex w-full items-start gap-3 px-4 py-3 text-left transition-colors',
                  selectedId === entry.id && 'bg-accent/60',
                )}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    {entry.strategy?.color ? (
                      <span
                        className="h-2 w-2 shrink-0 rounded-full"
                        style={{ backgroundColor: entry.strategy.color }}
                      />
                    ) : null}
                    <p className="truncate text-sm font-medium">{entry.title}</p>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    {entry.symbol ? (
                      <span className="text-muted-foreground text-xs">{entry.symbol}</span>
                    ) : null}
                    <span className="text-muted-foreground text-xs">{entry.session_date}</span>
                    {entry.grade ? (
                      <span className="text-[10px] text-amber-400">{formatGrade(entry.grade)}</span>
                    ) : null}
                    {entry.source === 'auto_import' ? (
                      <Badge variant="outline" className="text-[10px]">
                        auto
                      </Badge>
                    ) : null}
                    {entry.screenshots.length > 0 ? (
                      <Camera className="text-muted-foreground h-3 w-3" />
                    ) : null}
                  </div>
                  {entry.tags && entry.tags.length > 0 ? (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {entry.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-[10px]">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {entry.pnl !== null ? (
                    <span
                      className={cn(
                        'text-sm font-semibold tabular-nums',
                        entry.pnl >= 0 ? 'text-profit' : 'text-loss',
                      )}
                    >
                      {entry.pnl >= 0 ? '+' : ''}
                      {formatCurrency(entry.pnl)}
                    </span>
                  ) : null}
                  <ChevronRight className="text-muted-foreground h-4 w-4" />
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
