import type { ReactNode } from 'react';
import Link from 'next/link';

import { cn } from '@tradeflow/ui';

import { ThemeToggle } from '@/components/theme-toggle';

interface LegalDocumentLayoutProps {
  title: string;
  updated: string;
  children: ReactNode;
}

export function LegalDocumentLayout({ title, updated, children }: LegalDocumentLayoutProps) {
  return (
    <div className="bg-background text-foreground min-h-screen">
      <header className="border-border border-b">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-3 px-6">
          <Link href="/" className="text-sm font-semibold">
            TradeFlow AI
          </Link>
          <div className="flex items-center gap-3">
            <nav className="text-muted-foreground flex gap-4 text-xs">
              <Link href="/terms" className="hover:text-foreground">
                Terms
              </Link>
              <Link href="/privacy" className="hover:text-foreground">
                Privacy
              </Link>
              <Link href="/risk-disclosure" className="hover:text-foreground">
                Risk
              </Link>
            </nav>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-muted-foreground text-xs uppercase tracking-wider">Legal</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">{title}</h1>
        <p className="text-muted-foreground mt-2 text-sm">Last updated: {updated}</p>
        <article
          className={cn(
            'prose prose-sm dark:prose-invert mt-10 max-w-none',
            'prose-headings:font-semibold prose-headings:tracking-tight',
            'prose-p:text-muted-foreground prose-li:text-muted-foreground',
            'prose-a:text-indigo-500 dark:prose-a:text-indigo-400',
            'prose-strong:text-foreground',
          )}
        >
          {children}
        </article>
      </main>
    </div>
  );
}
