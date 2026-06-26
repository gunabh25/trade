'use client';

import type { ComponentType } from 'react';

import {
  AlertTriangle,
  BookMarked,
  Camera,
  Lightbulb,
  Pencil,
  StickyNote,
  Tag,
  Upload,
} from 'lucide-react';
import { useMemo, useRef, useState } from 'react';

import type { JournalEntry } from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Separator,
  cn,
} from '@tradeflow/ui';

import { getScreenshotUrl, uploadJournalScreenshot } from '@/features/journal/api/journal-api';
import { renderMarkdown } from '@/features/journal/lib/markdown';
import { formatCurrency, formatGrade } from '@/features/journal/utils/format';

interface JournalEntryDetailProps {
  entry: JournalEntry | null;
  onEdit: (entry: JournalEntry) => void;
  onUpdated: (entry: JournalEntry) => void;
}

export function JournalEntryDetail({ entry, onEdit, onUpdated }: JournalEntryDetailProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const contentHtml = useMemo(
    () => (entry?.content ? renderMarkdown(entry.content) : ''),
    [entry?.content],
  );
  const lessonsHtml = useMemo(
    () => (entry?.lessons_learned ? renderMarkdown(entry.lessons_learned) : ''),
    [entry?.lessons_learned],
  );

  if (!entry) {
    return (
      <Card className="border-border/60 bg-card/80 flex h-full min-h-[420px] shadow-none md:min-h-[520px]">
        <CardContent className="text-muted-foreground flex flex-1 flex-col items-center justify-center">
          <StickyNote className="mb-3 h-10 w-10 opacity-40" />
          <p className="text-sm">Select a trade to view details</p>
          <p className="text-muted-foreground mt-1 text-xs">
            Press j/k to navigate · n for new entry
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const updated = await uploadJournalScreenshot(entry.id, file);
      onUpdated(updated);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <CardTitle className="text-lg font-semibold">{entry.title}</CardTitle>
            <CardDescription className="mt-1">
              {entry.session_date}
              {entry.symbol ? ` · ${entry.symbol}` : ''}
              {entry.side ? ` · ${entry.side.toUpperCase()}` : ''}
              {entry.quantity ? ` · ${String(entry.quantity)} qty` : ''}
            </CardDescription>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
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
            {entry.grade ? (
              <span className="text-sm text-amber-400">{formatGrade(entry.grade)}</span>
            ) : null}
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => {
                onEdit(entry);
              }}
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          </div>
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
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Entry" value={entry.entry_price?.toFixed(2) ?? '—'} />
          <Stat label="Exit" value={entry.exit_price?.toFixed(2) ?? '—'} />
          <Stat label="Mood" value={entry.mood ?? '—'} />
          <Stat label="Source" value={entry.source === 'auto_import' ? 'Auto' : 'Manual'} />
        </div>

        {entry.content ? (
          <MarkdownSection icon={BookMarked} title="Trade Notes" html={contentHtml} />
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
          <MarkdownSection icon={Lightbulb} title="Lessons Learned" html={lessonsHtml} accent />
        ) : null}

        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-muted-foreground flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
              <Camera className="h-3 w-3" />
              Screenshots
            </p>
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-3 w-3" />
              {uploading ? 'Uploading…' : 'Upload'}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleUpload(file);
                e.target.value = '';
              }}
            />
          </div>
          {entry.screenshots.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {entry.screenshots.map((shot) => (
                <a
                  key={shot.id}
                  href={getScreenshotUrl(shot.file_url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="border-border/60 group overflow-hidden rounded-lg border"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getScreenshotUrl(shot.file_url)}
                    alt={shot.caption ?? 'Trade screenshot'}
                    className="aspect-video w-full object-cover transition-opacity group-hover:opacity-90"
                  />
                  {shot.caption ? (
                    <p className="text-muted-foreground truncate px-2 py-1 text-[10px]">
                      {shot.caption}
                    </p>
                  ) : null}
                </a>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-xs">No screenshots yet</p>
          )}
        </div>

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

function MarkdownSection({
  icon: Icon,
  title,
  html,
  accent,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  html: string;
  accent?: boolean;
}) {
  return (
    <div>
      <p className="text-muted-foreground mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wider">
        <Icon className="h-3 w-3" />
        {title}
      </p>
      <div
        className={cn(
          'prose prose-invert prose-sm max-w-none rounded-md border px-3 py-2 text-sm leading-relaxed',
          accent ? 'bg-profit/5 border-profit/20' : 'border-border/60',
        )}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
