'use client';

import { Download, FileText, Loader2, Plus, Search, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';

import {
  Badge,
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Input,
  ScrollArea,
  cn,
} from '@tradeflow/ui';

import { downloadJournalExport } from '@/features/journal/api/journal-api';
import { EMOTIONS } from '@/features/journal/constants';
import type { JournalData } from '@/features/journal/hooks/use-journal-data';

interface JournalFiltersProps {
  data: JournalData;
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  onNewEntry: () => void;
  onImport: () => void;
  importing?: boolean;
}

export function JournalFilters({
  data,
  searchInputRef,
  onNewEntry,
  onImport,
  importing,
}: JournalFiltersProps) {
  const localRef = useRef<HTMLInputElement>(null);
  const inputRef = searchInputRef ?? localRef;
  const [exporting, setExporting] = useState<'csv' | 'pdf' | null>(null);

  const hasFilters =
    data.search.length > 0 ||
    data.selectedTag !== null ||
    data.selectedStrategy !== null ||
    data.selectedEmotion !== null;

  const handleExport = async (format: 'csv' | 'pdf') => {
    setExporting(format);
    try {
      await downloadJournalExport(format, {
        ...(data.search ? { q: data.search } : {}),
        ...(data.selectedStrategy ? { strategy_id: data.selectedStrategy } : {}),
        ...(data.selectedTag ? { tag: data.selectedTag } : {}),
        ...(data.selectedEmotion ? { emotion: data.selectedEmotion } : {}),
      });
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
          <Input
            ref={inputRef}
            placeholder="Search trades, notes, tags, lessons… (/)"
            value={data.search}
            onChange={(e) => {
              data.setSearch(e.target.value);
            }}
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            disabled={importing}
            onClick={onImport}
          >
            {importing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">Import Trades</span>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5">
                {exporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                <span className="hidden sm:inline">Export</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => void handleExport('csv')}>
                <FileText className="mr-2 h-4 w-4" />
                Export CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => void handleExport('pdf')}>
                <FileText className="mr-2 h-4 w-4" />
                Export PDF
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button size="sm" className="gap-1.5" onClick={onNewEntry}>
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

      <ScrollArea className="w-full whitespace-nowrap lg:hidden">
        <div className="flex gap-2 pb-1">
          <FilterChip
            label="All Emotions"
            active={!data.selectedEmotion}
            onClick={() => {
              data.setSelectedEmotion(null);
            }}
          />
          {EMOTIONS.map((emotion) => (
            <FilterChip
              key={emotion}
              label={emotion}
              active={data.selectedEmotion === emotion}
              onClick={() => {
                data.setSelectedEmotion(data.selectedEmotion === emotion ? null : emotion);
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
            data.setSelectedEmotion(null);
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
          <FilterChip
            label="All"
            active={!data.selectedEmotion}
            onClick={() => {
              data.setSelectedEmotion(null);
            }}
          />
          {EMOTIONS.map((emotion) => (
            <Badge
              key={emotion}
              variant={data.selectedEmotion === emotion ? 'default' : 'outline'}
              className="cursor-pointer text-[10px] capitalize"
              onClick={() => {
                data.setSelectedEmotion(data.selectedEmotion === emotion ? null : emotion);
              }}
            >
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
        'inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors',
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
