'use client';

import { cn } from '@tradeflow/ui';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';

const SIDEBAR_ITEMS = ['Overview', 'Copier', 'Risk', 'Journal', 'Analytics'] as const;

const EQUITY_BARS = [35, 42, 38, 55, 48, 62, 58, 72, 68, 80, 75, 88, 82, 90, 85, 92];

function WindowChrome() {
  return (
    <div className="flex items-center gap-2 border-b border-white/[0.06] px-3 py-2.5 sm:px-4 sm:py-3">
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <div className="h-2 w-2 rounded-full bg-red-500/80 sm:h-2.5 sm:w-2.5" />
        <div className="h-2 w-2 rounded-full bg-amber-500/80 sm:h-2.5 sm:w-2.5" />
        <div className="h-2 w-2 rounded-full bg-emerald-500/80 sm:h-2.5 sm:w-2.5" />
      </div>
      <span className="ml-1 truncate text-[10px] text-zinc-600 sm:ml-2 sm:text-[11px]">
        <span className="sm:hidden">TradeFlow</span>
        <span className="hidden sm:inline">TradeFlow — Unified Terminal</span>
      </span>
    </div>
  );
}

function MobileNav() {
  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-white/[0.06] p-2 md:hidden">
      {SIDEBAR_ITEMS.map((item, i) => (
        <div
          key={item}
          className={cn(
            'shrink-0 rounded-lg px-2.5 py-1.5 text-[10px] font-medium sm:px-3 sm:text-[11px]',
            i === 0 ? 'bg-indigo-500/15 text-indigo-300' : 'text-zinc-600',
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
    <aside className="hidden w-[132px] shrink-0 border-r border-white/[0.06] p-3 md:block lg:w-[148px]">
      <nav className="space-y-1">
        {SIDEBAR_ITEMS.map((item, i) => (
          <div
            key={item}
            className={cn(
              'rounded-lg px-3 py-2 text-[11px] font-medium',
              i === 0 ? 'bg-indigo-500/15 text-indigo-300' : 'text-zinc-600',
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
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Open P&amp;L
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums text-teal-400 sm:text-xl">
            +$4,280
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Accounts
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums text-white sm:text-xl">12</p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 sm:px-4 sm:py-3">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Fill Rate
          </p>
          <p className="mt-1 text-lg font-semibold tabular-nums text-white sm:text-xl">99.8%</p>
        </div>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 sm:p-4">
        <p className="text-[10px] font-medium text-zinc-500">Equity Curve</p>
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
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 sm:p-4">
          <p className="text-[10px] font-medium text-zinc-600">Active Copier</p>
          <div className="mt-2 space-y-1">
            <p className="text-[10px] text-zinc-400 sm:text-[11px]">ES — 4 accounts</p>
            <p className="text-[10px] text-zinc-400 sm:text-[11px]">NQ — 3 accounts</p>
          </div>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 sm:p-4">
          <p className="text-[10px] font-medium text-zinc-600">Risk Status</p>
          <p className="mt-2 text-[10px] text-emerald-400 sm:text-[11px]">All limits OK</p>
          <p className="text-[10px] text-zinc-500 sm:text-[11px]">Max DD: 2.1%</p>
        </div>
      </div>
    </div>
  );
}

function PreviewOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-[#05070a]/55 p-4 backdrop-blur-[6px]">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="max-w-xs text-center sm:max-w-sm"
      >
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-white/15 bg-white/[0.06] shadow-lg backdrop-blur-sm sm:mb-5 sm:h-14 sm:w-14">
          <Play className="ml-0.5 h-4 w-4 text-white sm:h-5 sm:w-5" fill="white" />
        </div>
        <h3 className="text-base font-semibold tracking-tight text-white sm:text-lg md:text-xl">
          Unified Terminal Preview
        </h3>
        <p className="mx-auto mt-2 text-xs leading-relaxed text-zinc-400 sm:text-sm">
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
        className="relative overflow-hidden rounded-xl border border-white/[0.08] bg-[#0a0d14] shadow-[0_20px_60px_rgba(0,0,0,0.5),0_0_32px_rgba(34,211,238,0.06)] sm:rounded-2xl"
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
