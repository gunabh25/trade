'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

import type { HealthSummaryResponse, ReadinessResponse } from '@tradeflow/types/api';
import { cn } from '@tradeflow/ui';

import { fetchHealthSummary, fetchReadiness } from '@/features/health/api/health-api';

function StatusBadge({ status }: { status: string }) {
  const healthy = status === 'healthy' || status === 'alive' || status === 'ok';
  const degraded = status === 'degraded';
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        healthy && 'bg-emerald-500/15 text-emerald-400',
        degraded && 'bg-amber-500/15 text-amber-400',
        !healthy && !degraded && 'bg-red-500/15 text-red-400',
      )}
    >
      {healthy ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
      {status}
    </span>
  );
}

export function StatusPageContent() {
  const [summary, setSummary] = useState<HealthSummaryResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [webOk, setWebOk] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [summaryResult, readinessResult, webHealth] = await Promise.all([
          fetchHealthSummary(),
          fetchReadiness(),
          fetch('/api/health').then((r) => r.json() as Promise<{ status: string }>),
        ]);
        setSummary(summaryResult);
        setReadiness(readinessResult);
        setWebOk(webHealth.status === 'ok');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load status');
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <div className="min-h-screen bg-[#05070a] text-zinc-200">
      <header className="border-b border-white/[0.06]">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-6">
          <Link href="/" className="text-sm font-semibold text-white">
            TradeFlow AI
          </Link>
          <Link href="/login" className="text-xs text-zinc-500 hover:text-white">
            Login
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-3xl font-semibold tracking-tight text-white">System Status</h1>
        <p className="mt-2 text-sm text-zinc-500">
          Live health checks for TradeFlow web and API services.
        </p>

        {loading ? (
          <div className="text-muted-foreground mt-12 flex items-center gap-2 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            Checking services…
          </div>
        ) : null}

        {error ? (
          <p className="mt-8 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </p>
        ) : null}

        {!loading && !error ? (
          <div className="mt-10 space-y-4">
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">Web Application</p>
                  <p className="text-xs text-zinc-500">tradeflow-web</p>
                </div>
                <StatusBadge status={webOk ? 'ok' : 'unhealthy'} />
              </div>
            </div>

            {summary ? (
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">API</p>
                    <p className="text-xs text-zinc-500">
                      {summary.service} · v{summary.version} · {summary.environment}
                    </p>
                  </div>
                  <StatusBadge status={summary.status} />
                </div>
              </div>
            ) : null}

            {readiness ? (
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
                <p className="mb-4 font-medium text-white">Dependencies</p>
                <div className="space-y-3 text-sm">
                  {(['database', 'redis'] as const).map((key) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="capitalize text-zinc-400">{key}</span>
                      <div className="flex items-center gap-3">
                        {readiness.checks[key].latencyMs != null ? (
                          <span className="text-xs text-zinc-600">
                            {readiness.checks[key].latencyMs}ms
                          </span>
                        ) : null}
                        <StatusBadge status={readiness.checks[key].status} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <p className="text-xs text-zinc-600">
              Last checked: {summary?.timestamp ?? new Date().toISOString()}
            </p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
