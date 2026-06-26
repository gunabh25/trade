'use client';

import { Download, Plus, Search, X } from 'lucide-react';

import { Badge, Button, Input, ScrollArea, cn } from '@tradeflow/ui';

import { EMOTIONS } from '@/features/journal/data/mock-journal-data';
import type { JournalData } from '@/features/journal/hooks/use-journal-data';

interface JournalFiltersProps {
  data: JournalData;
}

export function JournalFilters({ data }: JournalFiltersProps) {
  const hasFilters =
    data.search.length > 0 || data.selectedTag !== null || data.selectedStrategy !== null;

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
          <Input
            placeholder="Search trades, notes, tags, lessons..."
            value={data.search}
            onChange={(e) => {
              data.setSearch(e.target.value);
            }}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1.5">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Import Trades</span>
          </Button>
          <Button size="sm" className="gap-1.5">
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">New Entry</span>
          </Button>
        </div>
      </div>

      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex gap-2 pb-1">
          <FilterChip
            label="All Strategies"
            active={!data.selectedStrategy}
            onClick={() => {
              data.setSelectedStrategy(null);
            }}
          />
          {data.strategies.map((s) => (
            <FilterChip
              key={s.id}
              label={s.name}
              active={data.selectedStrategy === s.id}
              {...(s.color ? { color: s.color } : {})}
              onClick={() => {
                data.setSelectedStrategy(data.selectedStrategy === s.id ? null : s.id);
              }}
            />
          ))}
        </div>
      </ScrollArea>

      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex gap-2 pb-1">
          <FilterChip
            label="All Tags"
            active={!data.selectedTag}
            onClick={() => {
              data.setSelectedTag(null);
            }}
          />
          {data.tags.map((tag) => (
            <FilterChip
              key={tag}
              label={`#${tag}`}
              active={data.selectedTag === tag}
              onClick={() => {
                data.setSelectedTag(data.selectedTag === tag ? null : tag);
              }}
            />
          ))}
        </div>
      </ScrollArea>

      {hasFilters ? (
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground h-7 gap-1 px-2 text-xs"
          onClick={() => {
            data.setSearch('');
            data.setSelectedTag(null);
            data.setSelectedStrategy(null);
          }}
        >
          <X className="h-3 w-3" />
          Clear filters
        </Button>
      ) : null}

      <div className="hidden lg:block">
        <p className="text-muted-foreground mb-2 text-xs font-medium uppercase tracking-wider">
          Emotions
        </p>
        <div className="flex flex-wrap gap-1.5">
          {EMOTIONS.map((emotion) => (
            <Badge key={emotion} variant="outline" className="text-[10px] capitalize">
              {emotion}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}

function FilterChip({
  label,
  active,
  onClick,
  color,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  color?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
        active
          ? 'border-primary/50 bg-primary/10 text-foreground'
          : 'border-border/60 text-muted-foreground hover:border-border hover:text-foreground',
      )}
    >
      {color ? <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} /> : null}
      {label}
    </button>
  );
}
