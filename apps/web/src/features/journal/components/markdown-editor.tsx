'use client';

import { Eye, Pencil } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button, cn } from '@tradeflow/ui';

import { renderMarkdown } from '@/features/journal/lib/markdown';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minHeight?: string;
}

export function MarkdownEditor({
  value,
  onChange,
  placeholder = 'Write trade notes in markdown…',
  minHeight = '160px',
}: MarkdownEditorProps) {
  const [mode, setMode] = useState<'write' | 'preview'>('write');
  const previewHtml = useMemo(() => renderMarkdown(value || ''), [value]);

  return (
    <div className="border-border/60 rounded-lg border">
      <div className="border-border/60 flex items-center justify-between border-b px-2 py-1">
        <p className="text-muted-foreground px-1 text-[10px] font-medium uppercase tracking-wider">
          Markdown
        </p>
        <div className="flex gap-1">
          <Button
            type="button"
            variant={mode === 'write' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => {
              setMode('write');
            }}
          >
            <Pencil className="h-3 w-3" />
            Write
          </Button>
          <Button
            type="button"
            variant={mode === 'preview' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => {
              setMode('preview');
            }}
          >
            <Eye className="h-3 w-3" />
            Preview
          </Button>
        </div>
      </div>
      {mode === 'write' ? (
        <textarea
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
          }}
          placeholder={placeholder}
          className="bg-background placeholder:text-muted-foreground w-full resize-y rounded-b-lg px-3 py-2 text-sm outline-none"
          style={{ minHeight }}
        />
      ) : (
        <div
          className={cn(
            'prose prose-invert prose-sm max-w-none px-3 py-2 text-sm leading-relaxed',
            !value && 'text-muted-foreground italic',
          )}
          style={{ minHeight }}
          {...(value
            ? { dangerouslySetInnerHTML: { __html: previewHtml } }
            : { children: 'Nothing to preview yet.' })}
        />
      )}
    </div>
  );
}
