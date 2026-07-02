import type { ReactNode } from 'react';
import Link from 'next/link';

import { cn } from '@tradeflow/ui';

interface LegalDocumentLayoutProps {
  title: string;
  updated: string;
  children: ReactNode;
}

export function LegalDocumentLayout({ title, updated, children }: LegalDocumentLayoutProps) {
  return (
    <div className="min-h-screen bg-[#05070a] text-zinc-200">
      <header className="border-b border-white/[0.06]">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-6">
          <Link href="/" className="text-sm font-semibold text-white">
            TradeFlow AI
          </Link>
          <nav className="flex gap-4 text-xs text-zinc-500">
            <Link href="/terms" className="hover:text-white">
              Terms
            </Link>
            <Link href="/privacy" className="hover:text-white">
              Privacy
            </Link>
            <Link href="/risk-disclosure" className="hover:text-white">
              Risk
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-xs uppercase tracking-wider text-zinc-500">Legal</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">{title}</h1>
        <p className="mt-2 text-sm text-zinc-500">Last updated: {updated}</p>
        <article
          className={cn(
            'prose prose-invert prose-sm mt-10 max-w-none',
            'prose-headings:font-semibold prose-headings:tracking-tight',
            'prose-p:text-zinc-400 prose-li:text-zinc-400',
            'prose-a:text-indigo-400 prose-strong:text-zinc-200',
          )}
        >
          {children}
        </article>
      </main>
    </div>
  );
}
