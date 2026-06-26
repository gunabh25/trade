'use client';

import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import type {
  CreateJournalEntryPayload,
  JournalEntry,
  JournalStrategy,
} from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Input,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  cn,
} from '@tradeflow/ui';

import { createJournalEntry, updateJournalEntry } from '@/features/journal/api/journal-api';
import { MarkdownEditor } from '@/features/journal/components/markdown-editor';
import { COMMON_MISTAKES, EMOTIONS, GRADE_OPTIONS } from '@/features/journal/constants';

interface JournalEntryFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategies: JournalStrategy[];
  existingTags: string[];
  entry?: JournalEntry | null;
  onSaved: (entry: JournalEntry) => void;
}

const EMPTY_FORM: CreateJournalEntryPayload = {
  title: '',
  session_date: new Date().toISOString().slice(0, 10),
  content: '',
  notes: '',
  symbol: '',
  side: 'long',
  pnl: null,
  grade: null,
  tags: [],
  emotions: [],
  mistakes: [],
  lessons_learned: '',
  strategy_id: null,
};

export function JournalEntryForm({
  open,
  onOpenChange,
  strategies,
  existingTags,
  entry,
  onSaved,
}: JournalEntryFormProps) {
  const [form, setForm] = useState<CreateJournalEntryPayload>(EMPTY_FORM);
  const [tagInput, setTagInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isEdit = Boolean(entry);

  useEffect(() => {
    if (!open) return;
    if (entry) {
      setForm({
        title: entry.title,
        session_date: entry.session_date,
        content: entry.content ?? '',
        notes: entry.notes ?? '',
        mood: entry.mood,
        symbol: entry.symbol ?? '',
        side: entry.side ?? 'long',
        quantity: entry.quantity,
        entry_price: entry.entry_price,
        exit_price: entry.exit_price,
        pnl: entry.pnl,
        grade: entry.grade,
        tags: entry.tags ?? [],
        emotions: entry.emotions ?? [],
        mistakes: entry.mistakes ?? [],
        lessons_learned: entry.lessons_learned ?? '',
        strategy_id: entry.strategy_id,
      });
    } else {
      setForm({ ...EMPTY_FORM, session_date: new Date().toISOString().slice(0, 10) });
    }
    setError(null);
  }, [open, entry]);

  const toggleListItem = (field: 'emotions' | 'mistakes' | 'tags', value: string) => {
    setForm((current) => {
      const list = current[field] ?? [];
      const next = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
      return { ...current, [field]: next };
    });
  };

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (!tag) return;
    toggleListItem('tags', tag);
    setTagInput('');
  };

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.title.trim()) {
      setError('Title is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: CreateJournalEntryPayload = {
        ...form,
        title: form.title.trim(),
        symbol: form.symbol?.trim() ? form.symbol : null,
        content: form.content?.trim() ? form.content : null,
        notes: form.notes?.trim() ? form.notes : null,
        lessons_learned: form.lessons_learned?.trim() ? form.lessons_learned : null,
      };
      const saved = entry
        ? await updateJournalEntry(entry.id, payload)
        : await createJournalEntry(payload);
      onSaved(saved);
      onOpenChange(false);
    } catch {
      setError('Failed to save entry');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>{isEdit ? 'Edit Journal Entry' : 'New Journal Entry'}</SheetTitle>
        </SheetHeader>

        <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-5">
          <Field label="Title">
            <Input
              value={form.title}
              onChange={(e) => {
                setForm({ ...form, title: e.target.value });
              }}
              placeholder="ES Long — ORB Breakout"
              required
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Session Date">
              <Input
                type="date"
                value={form.session_date}
                onChange={(e) => {
                  setForm({ ...form, session_date: e.target.value });
                }}
                required
              />
            </Field>
            <Field label="Symbol">
              <Input
                value={form.symbol ?? ''}
                onChange={(e) => {
                  setForm({ ...form, symbol: e.target.value.toUpperCase() });
                }}
                placeholder="ES"
              />
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label="Side">
              <select
                className="border-input bg-background h-9 w-full rounded-md border px-2 text-sm"
                value={form.side ?? 'long'}
                onChange={(e) => {
                  setForm({ ...form, side: e.target.value });
                }}
              >
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
            </Field>
            <Field label="P&L">
              <Input
                type="number"
                step="0.01"
                value={form.pnl ?? ''}
                onChange={(e) => {
                  setForm({
                    ...form,
                    pnl: e.target.value === '' ? null : Number(e.target.value),
                  });
                }}
              />
            </Field>
            <Field label="Strategy">
              <select
                className="border-input bg-background h-9 w-full rounded-md border px-2 text-sm"
                value={form.strategy_id ?? ''}
                onChange={(e) => {
                  setForm({ ...form, strategy_id: e.target.value || null });
                }}
              >
                <option value="">None</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Trade Grade">
            <div className="flex gap-1">
              {GRADE_OPTIONS.map((grade) => (
                <button
                  key={grade}
                  type="button"
                  onClick={() => {
                    setForm({ ...form, grade: form.grade === grade ? null : grade });
                  }}
                  className={cn(
                    'rounded-md border px-2 py-1 text-xs transition-colors',
                    form.grade === grade
                      ? 'border-primary bg-primary/10 text-foreground'
                      : 'border-border/60 text-muted-foreground hover:border-border',
                  )}
                >
                  {'★'.repeat(grade)}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Trade Notes">
            <MarkdownEditor
              value={form.content ?? ''}
              onChange={(content) => {
                setForm({ ...form, content });
              }}
            />
          </Field>

          <Field label="Lessons Learned">
            <MarkdownEditor
              value={form.lessons_learned ?? ''}
              onChange={(lessons_learned) => {
                setForm({ ...form, lessons_learned });
              }}
              placeholder="What did you learn from this trade?"
              minHeight="100px"
            />
          </Field>

          <Field label="Emotions">
            <div className="flex flex-wrap gap-1.5">
              {EMOTIONS.map((emotion) => (
                <Badge
                  key={emotion}
                  variant={form.emotions?.includes(emotion) ? 'default' : 'outline'}
                  className="cursor-pointer capitalize"
                  onClick={() => {
                    toggleListItem('emotions', emotion);
                  }}
                >
                  {emotion}
                </Badge>
              ))}
            </div>
          </Field>

          <Field label="Mistakes">
            <div className="flex flex-wrap gap-1.5">
              {COMMON_MISTAKES.map((mistake) => (
                <Badge
                  key={mistake}
                  variant={form.mistakes?.includes(mistake) ? 'destructive' : 'outline'}
                  className="cursor-pointer capitalize"
                  onClick={() => {
                    toggleListItem('mistakes', mistake);
                  }}
                >
                  {mistake}
                </Badge>
              ))}
            </div>
          </Field>

          <Field label="Tags">
            <div className="flex gap-2">
              <Input
                value={tagInput}
                onChange={(e) => {
                  setTagInput(e.target.value);
                }}
                placeholder="Add tag…"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTag();
                  }
                }}
              />
              <Button type="button" variant="outline" onClick={addTag}>
                Add
              </Button>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {[...new Set([...existingTags, ...(form.tags ?? [])])].slice(0, 12).map((tag) => (
                <Badge
                  key={tag}
                  variant={form.tags?.includes(tag) ? 'secondary' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => {
                    toggleListItem('tags', tag);
                  }}
                >
                  #{tag}
                </Badge>
              ))}
            </div>
          </Field>

          {error ? <p className="text-loss text-sm">{error}</p> : null}

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={saving} className="flex-1">
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isEdit ? (
                'Save Changes'
              ) : (
                'Create Entry'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                onOpenChange(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-muted-foreground mb-1.5 block text-xs font-medium uppercase tracking-wider">
        {label}
      </label>
      {children}
    </div>
  );
}
