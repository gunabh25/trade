'use client';

import type { ComponentType } from 'react';

import { AlertTriangle, BookMarked, Lightbulb, StickyNote, Tag } from 'lucide-react';

import type { JournalEntry } from '@tradeflow/types/api';

import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Separator,
  cn,
} from '@tradeflow/ui';

import { formatCurrency } from '@/features/journal/data/mock-journal-data';

interface JournalEntryDetailProps {
  entry: JournalEntry | null;
}

export function JournalEntryDetail({ entry }: JournalEntryDetailProps) {
  if (!entry) {
    return (
      <Card className="border-border/60 bg-card/80 flex h-full min-h-[420px] shadow-none md:min-h-[520px]">
        <CardContent className="text-muted-foreground flex flex-1 flex-col items-center justify-center">
          <StickyNote className="mb-3 h-10 w-10 opacity-40" />
          <p className="text-sm">Select a trade to view details</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-semibold">{entry.title}</CardTitle>
            <CardDescription className="mt-1">
              {entry.session_date}
              {entry.symbol ? ` · ${entry.symbol}` : ''}
              {entry.side ? ` · ${entry.side.toUpperCase()}` : ''}
              {entry.quantity ? ` · ${String(entry.quantity)} qty` : ''}
            </CardDescription>
          </div>
          {entry.pnl !== null ? (
            <span
              className={cn(
                'text-xl font-bold tabular-nums',
                entry.pnl >= 0 ? 'text-profit' : 'text-loss',
              )}
            >
              {entry.pnl >= 0 ? '+' : ''}
              {formatCurrency(entry.pnl)}
            </span>
          ) : null}
        </div>
        {entry.strategy ? (
          <Badge
            variant="outline"
            className="mt-2 w-fit gap-1.5"
            style={{ borderColor: entry.strategy.color ?? undefined }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.strategy.color ?? '#64748b' }}
            />
            {entry.strategy.name}
          </Badge>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-5">
        {entry.entry_price && entry.exit_price ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Entry" value={entry.entry_price.toFixed(2)} />
            <Stat label="Exit" value={entry.exit_price.toFixed(2)} />
            <Stat label="Mood" value={entry.mood ?? '—'} />
            <Stat label="Source" value={entry.source === 'auto_import' ? 'Auto' : 'Manual'} />
          </div>
        ) : null}

        {entry.content ? (
          <Section icon={BookMarked} title="Trade Notes" content={entry.content} />
        ) : null}
        {entry.notes ? (
          <Section icon={StickyNote} title="Additional Notes" content={entry.notes} />
        ) : null}

        {entry.emotions && entry.emotions.length > 0 ? (
          <div>
            <p className="text-muted-foreground mb-2 text-xs font-medium uppercase tracking-wider">
              Emotions
            </p>
            <div className="flex flex-wrap gap-1.5">
              {entry.emotions.map((e) => (
                <Badge key={e} variant="secondary" className="capitalize">
                  {e}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {entry.tags && entry.tags.length > 0 ? (
          <div>
            <p className="text-muted-foreground mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
              <Tag className="h-3 w-3" />
              Tags
            </p>
            <div className="flex flex-wrap gap-1.5">
              {entry.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  #{tag}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {entry.mistakes && entry.mistakes.length > 0 ? (
          <div>
            <p className="text-muted-foreground mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
              <AlertTriangle className="h-3 w-3" />
              Mistakes
            </p>
            <ul className="space-y-1.5">
              {entry.mistakes.map((mistake) => (
                <li
                  key={mistake}
                  className="bg-loss/10 text-loss border-loss/20 rounded-md border px-3 py-2 text-sm"
                >
                  {mistake}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {entry.lessons_learned ? (
          <div>
            <p className="text-muted-foreground mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
              <Lightbulb className="h-3 w-3" />
              Lessons Learned
            </p>
            <p className="bg-profit/5 border-profit/20 rounded-md border px-3 py-2 text-sm leading-relaxed">
              {entry.lessons_learned}
            </p>
          </div>
        ) : null}

        <Separator />

        <p className="text-muted-foreground text-[10px]">
          Updated {new Date(entry.updated_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-muted/30 rounded-md px-3 py-2">
      <p className="text-muted-foreground text-[10px] uppercase tracking-wider">{label}</p>
      <p className="mt-0.5 text-sm font-medium capitalize">{value}</p>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  content,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  content: string;
}) {
  return (
    <div>
      <p className="text-muted-foreground mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
        <Icon className="h-3 w-3" />
        {title}
      </p>
      <p className="text-sm leading-relaxed">{content}</p>
    </div>
  );
}
