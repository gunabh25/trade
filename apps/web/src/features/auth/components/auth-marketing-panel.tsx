'use client';

import { motion } from 'framer-motion';
import { Activity, TrendingUp } from 'lucide-react';

function FloatingCard({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: 'easeOut' }}
      className={className}
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
}

export function AuthMarketingPanel() {
  return (
    <div className="relative hidden h-full flex-col items-center justify-center overflow-hidden border-l border-white/[0.06] bg-[#06080f] px-12 lg:flex">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.08)_0%,transparent_70%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_80%_20%,rgba(6,182,212,0.06)_0%,transparent_50%)]" />

      <div className="relative flex h-[320px] w-full max-w-md items-center justify-center">
        <div className="absolute h-64 w-64 rounded-full border border-white/[0.04]" />
        <div className="absolute h-48 w-48 rounded-full border border-white/[0.06]" />
        <div className="absolute h-32 w-32 rounded-full border border-indigo-500/20 bg-indigo-500/5" />

        <FloatingCard
          delay={0.2}
          className="absolute -right-2 top-8 z-10 rounded-xl border border-white/10 bg-[#0d1117]/90 px-4 py-3 shadow-2xl backdrop-blur-sm"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <span className="text-lg font-semibold tabular-nums text-emerald-400">+12.45%</span>
          </div>
        </FloatingCard>

        <FloatingCard
          delay={0.4}
          className="absolute -left-4 bottom-12 z-10 rounded-xl border border-white/10 bg-[#0d1117]/80 px-4 py-3 shadow-xl backdrop-blur-sm"
        >
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Activity className="h-3.5 w-3.5 text-indigo-400" />
            <span>3 accounts synced</span>
          </div>
        </FloatingCard>

        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="relative flex h-20 w-20 items-center justify-center rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-500/20 to-cyan-500/10 shadow-lg shadow-indigo-500/10"
        >
          <TrendingUp className="h-9 w-9 text-indigo-300" />
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="relative mt-10 max-w-sm text-center"
      >
        <h2 className="text-xl font-semibold tracking-tight text-white">
          Predictive Execution Engine
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-500">
          Join institutional traders synchronizing positions across global markets with
          sub-millisecond latency. High-fidelity copy trading at scale.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="relative mt-8 flex gap-3"
      >
        <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5 text-xs text-zinc-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Systems Operational
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5 text-xs text-zinc-400">
          <Activity className="h-3 w-3 text-indigo-400" />
          12ms Latency
        </div>
      </motion.div>
    </div>
  );
}
