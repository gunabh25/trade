'use client';

import { cn } from '@tradeflow/ui';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';

const SIDEBAR_ITEMS = ['Overview', 'Copier', 'Risk', 'Journal', 'Analytics'] as const;

const EQUITY_BARS = [35, 42, 38, 55, 48, 62, 58, 72, 68, 80, 75, 88, 82, 90, 85, 92];

function WindowChrome() {
  return (
    <div className="border-border flex items-center gap-2 border-b px-3 py-2.5 sm:px-4 sm:py-3">
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <div className="h-2 w-2 rounded-full bg-red-500/80 sm:h-2.5 sm:w-2.5" />
        <div className="h-2 w-2 rounded-full bg-amber-500/80 sm:h-2.5 sm:w-2.5" />
        <div className="h-2 w-2 rounded-full bg-emerald-500/80 sm:h-2.5 sm:w-2.5" />
      </div>
      <span className="text-muted-foreground ml-1 truncate text-[10px] sm:ml-2 sm:text-[11px]">
        <span className="sm:hidden">TradeFlow</span>
        <span className="hidden sm:inline">TradeFlow — Unified Terminal</span>
      </span>
    </div>
  );
}

function MobileNav() {
  return (
    <nav className="border-border flex gap-1 overflow-x-auto border-b p-2 md:hidden">
      {SIDEBAR_ITEMS.map((item, i) => (
        <div
          key={item}
          className={cn(
            'shrink-0 rounded-lg px-2.5 py-1.5 text-[10px] font-medium sm:px-3 sm:text-[11px]',
            i === 0
              ? 'bg-indigo-500/15 text-indigo-700 dark:text-indigo-300'
              : 'text-muted-foreground',
          )}
        >
          {item}
        </div>
      ))}
    </nav>
  );
}

function Sidebar() {
  return (
    <aside className="border-border hidden w-[132px] shrink-0 border-r p-3 md:block lg:w-[148px]">
      <nav className="space-y-1">
        {SIDEBAR_ITEMS.map((item, i) => (
          <div
            key={item}
            className={cn(
              'rounded-lg px-3 py-2 text-[11px] font-medium',
              i === 0
                ? 'bg-indigo-500/15 text-indigo-700 dark:text-indigo-300'
                : 'text-muted-foreground',
            )}
          >
            {item}
          </div>
        ))}
      </nav>
    </aside>
  );
}

function DashboardContent() {
  return (
    <div className="min-w-0 flex-1 space-y-2.5 p-3 sm:space-y-3 sm:p-4">
      <div className="grid grid-cols-1 gap-2 min-[420px]:grid-cols-3 sm:gap-3">
        <div className="border-border bg-muted/30 rounded-xl border px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-muted-foreground text-[9px] font-medium uppercase tracking-wider sm:text-[10px]">
            Open P&amp;L
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums text-teal-600 sm:text-xl dark:text-teal-400">
            +$4,280
          </p>
        </div>
        <div className="border-border bg-muted/30 rounded-xl border px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-muted-foreground text-[9px] font-medium uppercase tracking-wider sm:text-[10px]">
            Accounts
          </p>
          <p className="text-foreground mt-1 text-lg font-semibold tabular-nums sm:text-xl">12</p>
        </div>
        <div className="border-border bg-muted/30 rounded-xl border px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-muted-foreground text-[9px] font-medium uppercase tracking-wider sm:text-[10px]">
            Fill Rate
          </p>
          <p className="text-foreground mt-1 text-lg font-semibold tabular-nums sm:text-xl">
            99.8%
          </p>
        </div>
      </div>

      <div className="border-border bg-muted/30 rounded-xl border p-3 sm:p-4">
        <p className="text-muted-foreground text-[10px] font-medium">Equity Curve</p>
        <div className="mt-2 flex h-20 items-end gap-0.5 sm:mt-3 sm:h-24 sm:gap-1 md:h-28">
          {EQUITY_BARS.map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-sm bg-gradient-to-t from-cyan-600/50 via-cyan-500/70 to-teal-400/90 shadow-[0_-2px_8px_rgba(45,212,191,0.15)]"
              style={{ height: `${String(h)}%` }}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 min-[420px]:grid-cols-2 sm:gap-3">
        <div className="border-border bg-muted/30 rounded-xl border p-3 sm:p-4">
          <p className="text-muted-foreground text-[10px] font-medium">Active Copier</p>
          <div className="mt-2 space-y-1">
            <p className="text-muted-foreground text-[10px] sm:text-[11px]">ES — 4 accounts</p>
            <p className="text-muted-foreground text-[10px] sm:text-[11px]">NQ — 3 accounts</p>
          </div>
        </div>
        <div className="border-border bg-muted/30 rounded-xl border p-3 sm:p-4">
          <p className="text-muted-foreground text-[10px] font-medium">Risk Status</p>
          <p className="mt-2 text-[10px] text-emerald-600 sm:text-[11px] dark:text-emerald-400">
            All limits OK
          </p>
          <p className="text-muted-foreground text-[10px] sm:text-[11px]">Max DD: 2.1%</p>
        </div>
      </div>
    </div>
  );
}

function PreviewOverlay() {
  return (
    <div className="bg-background/55 absolute inset-0 flex items-center justify-center p-4 backdrop-blur-[6px]">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="max-w-xs text-center sm:max-w-sm"
      >
        <div className="bg-muted/50 border-border mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border shadow-lg backdrop-blur-sm sm:mb-5 sm:h-14 sm:w-14">
          <Play className="text-foreground ml-0.5 h-4 w-4 sm:h-5 sm:w-5" fill="currentColor" />
        </div>
        <h3 className="text-foreground text-base font-semibold tracking-tight sm:text-lg md:text-xl">
          Unified Terminal Preview
        </h3>
        <p className="text-muted-foreground mx-auto mt-2 text-xs leading-relaxed sm:text-sm">
          Monitor positions, risk, and copy performance from a single institutional-grade dashboard.
        </p>
      </motion.div>
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div className="relative mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="bg-cyan-500/8 pointer-events-none absolute inset-x-4 top-1/2 h-40 -translate-y-1/2 rounded-full blur-3xl sm:inset-x-12 sm:h-56" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="border-border bg-card relative overflow-hidden rounded-xl border shadow-lg sm:rounded-2xl dark:shadow-[0_20px_60px_rgba(0,0,0,0.5),0_0_32px_rgba(34,211,238,0.06)]"
      >
        <WindowChrome />
        <MobileNav />

        <div className="relative flex min-h-[320px] sm:min-h-[380px] md:min-h-[420px]">
          <Sidebar />
          <DashboardContent />
          <PreviewOverlay />
        </div>
      </motion.div>
    </div>
  );
}
