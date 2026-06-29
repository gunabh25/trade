'use client';

import { cn } from '@tradeflow/ui';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';

const SIDEBAR_ITEMS = ['Overview', 'Copier', 'Risk', 'Journal', 'Analytics'] as const;

const EQUITY_BARS = [35, 42, 38, 55, 48, 62, 58, 72, 68, 80, 75, 88, 82, 90, 85, 92];

function WindowChrome() {
  return (
    <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
      <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
      <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
      <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
      <span className="ml-2 text-[11px] text-zinc-600">TradeFlow — Unified Terminal</span>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="hidden w-[148px] shrink-0 border-r border-white/[0.06] p-3 md:block">
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
    <div className="min-w-0 flex-1 space-y-3 p-4">
      {/* KPI row */}
      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-3 sm:px-4">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Open P&amp;L
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums text-teal-400 sm:text-lg">
            +$4,280
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-3 sm:px-4">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Accounts
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums text-white sm:text-lg">12</p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-3 sm:px-4">
          <p className="text-[9px] font-medium uppercase tracking-wider text-zinc-600 sm:text-[10px]">
            Fill Rate
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums text-white sm:text-lg">99.8%</p>
        </div>
      </div>

      {/* Equity curve */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 sm:p-4">
        <p className="text-[10px] font-medium text-zinc-500">Equity Curve</p>
        <div className="mt-3 flex h-24 items-end gap-1 sm:h-28 sm:gap-1.5">
          {EQUITY_BARS.map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-sm bg-gradient-to-t from-cyan-600/50 via-cyan-500/70 to-teal-400/90 shadow-[0_-2px_8px_rgba(45,212,191,0.15)]"
              style={{ height: `${String(h)}%` }}
            />
          ))}
        </div>
      </div>

      {/* Bottom panels */}
      <div className="grid grid-cols-2 gap-2 sm:gap-3">
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
    <div className="absolute inset-0 flex items-center justify-center bg-[#05070a]/55 backdrop-blur-[6px]">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="px-6 text-center"
      >
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full border border-white/15 bg-white/[0.06] shadow-lg backdrop-blur-sm">
          <Play className="ml-0.5 h-5 w-5 text-white" fill="white" />
        </div>
        <h3 className="text-lg font-semibold tracking-tight text-white sm:text-xl">
          Unified Terminal Preview
        </h3>
        <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-zinc-400">
          Monitor positions, risk, and copy performance from a single institutional-grade dashboard.
        </p>
      </motion.div>
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div className="relative mx-auto max-w-4xl px-6 py-8 lg:px-8">
      <div className="bg-cyan-500/8 pointer-events-none absolute inset-x-12 top-1/2 h-56 -translate-y-1/2 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0d14] shadow-[0_20px_60px_rgba(0,0,0,0.5),0_0_32px_rgba(34,211,238,0.06)]"
      >
        <WindowChrome />

        <div className="relative flex min-h-[380px] sm:min-h-[420px]">
          <Sidebar />
          <DashboardContent />
          <PreviewOverlay />
        </div>
      </motion.div>
    </div>
  );
}
